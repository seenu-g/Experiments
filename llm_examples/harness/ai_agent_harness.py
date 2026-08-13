"""Standalone experiment harness for LLM tool-calling agent tasks -- modeled on
harness_demo.py's structure (self-contained, no imports from the shared
code_harness.py pipeline), but scoped specifically to testing whether a given
model can generate a working agentic tool-calling loop.

Why this exists as its own file: direct HTTP tests against Ollama showed
qwen2.5-coder:7b (the harness's default LOCAL_MODEL) writes a tool call's JSON
as plain `content` text instead of populating Ollama's structured `tool_calls`
field, while hermes3:latest does populate it correctly for the same request.
This script checks whether that gap shows up in *generated code* too, using
hermes3 as the model, before any of this gets folded into the shared harness.

STATIC CHECK vs EXECUTE are deliberately separate stages, not one combined
pass/fail: EXECUTE means actually running the generated agent loop, which
makes several REAL ollama.chat inference calls (2 per demo question) at
CPU-only speed on this machine. A retry loop that only finds out "was this
code even valid" by waiting out a 60s execution timeout wastes that whole
window rediscovering a bug (e.g. a missing import) that a static check --
ast.parse/py_compile plus resolve.py's undefined-name checks, all instant,
no model calls -- would have caught for free. So: GENERATE -> STATIC CHECK
(retry loop lives here) -> only once static checks pass, ASK before
EXECUTE -- execution is never automatic, since a correct agent's inference
time on this hardware can legitimately be long, and that's not something a
regenerate-and-retry loop should be burning attempts on.

The static-check logic below (ast.parse/py_compile plus the undefined-name
scan) is written fresh, inline, in this file -- deliberately NOT imported
from the shared harness's compile.py/resolve.py, even though the checks are
conceptually similar. This file has zero imports from and makes zero edits
to code_harness.py/generate.py/define.py/config.py/compile.py/resolve.py --
fully standalone, so nothing here can affect or depend on the shared
pipeline until hermes3's reliability on this machine is actually proven out.

Run: python ai_agent_harness.py
"""

import ast
import builtins
import os
import py_compile
import re
import shutil
import subprocess
import sys
import time

import ollama

_BUILTIN_NAMES = set(dir(builtins)) | {"__name__", "__file__", "__doc__"}

# =====================================================================
# GLOBAL CONFIGURATION
# =====================================================================
LOCAL_MODEL = "hermes3:latest"
RUN_ID = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "ai_agent_output", RUN_ID)

DEFAULT_TASK = (
    "Write a program that uses a local LLM with tool-calling to answer questions "
    "using four tools: getting the current date/time, performing a web search, "
    "getting system info of the laptop it runs on, and getting the list of currently "
    "running processes. Demonstrate the agent using at least one question that should "
    "route to each of the four tools."
)


# =====================================================================
# DEFINE -- restate + confirm the task before generating anything. Written
# fresh here, not imported from the shared harness's define.py, to keep this
# file fully standalone (see module docstring). Deliberately minimal: this
# script's GENERATE prompts are still hardcoded around the specific 4 tools
# in DEFAULT_TASK (web_search via ddgs, get_system_info via psutil, etc.),
# so this step confirms intent rather than trying to generalize to an
# arbitrary tool set the way define.py's full spec extraction does.
# =====================================================================
# Keyword-based, not model-based: the main harness's own define.py found LLM
# classification of "what external system/category is this" unreliable on a
# small local model (see define.py's _KNOWN_SYSTEM_KEYWORDS comment) and
# switched to deterministic keyword matching instead. Same reasoning here --
# only the two categories actually exercised by DEFAULT_TASK today. Add a
# new (pattern, category) entry, and a matching *_INSTRUCTION snippet below,
# only when a real task actually needs that category -- not speculatively.
_TOOL_TYPE_KEYWORDS = [
    (
        re.compile(
            r"date|time|system info|running processes|\bprocesses\b|laptop|cpu|memory|disk",
            re.IGNORECASE,
        ),
        "local_system_call",
    ),
    (re.compile(r"web search|search the web|internet search", re.IGNORECASE), "no_auth_api"),
]


def classify_tool_types(description: str) -> set:
    """Returns the set of tool-type categories DEFAULT_TASK's own wording
    matches. Falls back to both known categories if nothing matched, rather
    than silently building agent_tools.py with no type-specific guidance at
    all for a description that phrased things differently than expected."""
    matched = {name for pattern, name in _TOOL_TYPE_KEYWORDS if pattern.search(description)}
    return matched or {name for _, name in _TOOL_TYPE_KEYWORDS}


def describe_tool_type_matches(description: str) -> list:
    """Returns [(matched_text, category), ...] -- which specific words in the
    description matched which tool-type category, so DEFINE can show exactly
    what it identified rather than just the category names."""
    return [
        (match.group(0), category)
        for pattern, category in _TOOL_TYPE_KEYWORDS
        for match in pattern.finditer(description)
    ]


def define_task() -> str:
    """Show the definition FIRST, then ask for input -- reversed from asking
    first and only explaining afterward. No LLM call here: tool-calling
    itself needs a real LLM decision (that's the whole point -- without one
    this would just be a fixed procedural call), but classifying which part
    of the TEXT maps to which tool type is deterministic and reuses the same
    classify_tool_types() that actually gates GENERATE's instructions, so
    what's shown here is exactly what will be used, not a separate guess."""
    print(f"Default task:\n{DEFAULT_TASK}\n")
    print(
        f"Tool-calling requires a real LLM in the loop to decide which tool(s) to call -- "
        f"without one this is just a fixed procedural call, not an agent. Model: {LOCAL_MODEL} "
        f"(via Ollama).\n"
    )
    print("Default task's tool-to-prompt mapping:")
    for text, category in describe_tool_type_matches(DEFAULT_TASK):
        print(f"  '{text}' -> {category}")

    description = input("\nDescribe the agent task (blank = use default above): ").strip()
    if not description:
        return DEFAULT_TASK

    matches = describe_tool_type_matches(description)
    print("\nYour task's tool-to-prompt mapping:")
    if matches:
        for text, category in matches:
            print(f"  '{text}' -> {category}")
    else:
        print("  (no known tool type matched -- falling back to all known types)")

    return description


TOOLS_FILENAME = "agent_tools.py"
AGENT_FILENAME = "main.py"

_BASE_INSTRUCTION = (
    "You are an expert Python software engineer. Your task is to output ONLY valid, "
    "executable Python code, with no conversational preamble, explanations, or commentary. "
    "Every 'import' statement required by any function or standard-library call you use must "
    "be included at the top of the file. Never reference a module or name without importing it "
    "first. Output exactly one ```python ... ``` block."
)


def _ask(system_instruction: str, user_content: str, log) -> str:
    log(f"Querying {LOCAL_MODEL}...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"]


# =====================================================================
# GENERATE -- ROUND 1: agent_tools.py (TOOLS schema, the 4 real tool
# functions, TOOL_REGISTRY). This file only needs to know about the tools
# themselves -- nothing about ollama.chat or the agent loop.
# =====================================================================
_STRUCTURE_INSTRUCTION = (
    f"Write a single importable module, {TOOLS_FILENAME} -- no 'if __name__' block, this file "
    "is never run directly, only imported. Structure, regardless of which tools it contains:\n\n"
    "1. All tool functions defined FIRST, before TOOLS/TOOL_REGISTRY below them -- a dict/list "
    "literal evaluates immediately at module load, so referencing a function name before its "
    "own 'def' has run raises NameError.\n\n"
    "2. TOOLS = [ ... ] -- one dict per tool, in EXACTLY this shape (copy it, do not invent a "
    "different 'parameters' shape):\n"
    "   {'type': 'function', 'function': {'name': 'tool_name', 'description': '...', "
    "'parameters': {'type': 'object', 'properties': {}, 'required': []}}}\n"
    "   For a tool with an argument (e.g. a query string), 'properties' is not empty:\n"
    "   'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', "
    "'description': '...'}}, 'required': ['query']}\n"
    "   'parameters' MUST always be a dict shaped like the two examples above -- NEVER a bare "
    "list like [] or ['query']. A bare list has been observed before to fail with "
    "'pydantic_core.ValidationError: Input should be a valid dictionary'.\n\n"
    "3. TOOL_REGISTRY = {'tool_name': tool_function, ...} -- one entry per tool function above, "
    "this exact dict, this exact name. It has been observed missing before (defined nowhere "
    "despite being used elsewhere) -- double check it's actually present before finishing."
)

LOCAL_SYSTEM_CALL_INSTRUCTION = (
    "For any tool that reads THIS machine's own state (current date/time, system info, running "
    "processes) -- import platform and import psutil at the top (both already installed); this "
    "exact pair of imports has been observed missing before even though such tools use them, "
    "causing NameError. Use real values only (platform.system(), psutil.cpu_count(), "
    "psutil.virtual_memory(), psutil.disk_usage('/'), psutil.process_iter([\"pid\", \"name\"]) "
    "capped to the first 10, etc.) -- never hardcode or fake a value."
)

NO_AUTH_API_INSTRUCTION = (
    "For any web-search tool -- it must do a REAL search using the 'ddgs' package (already "
    "installed, no API key/credentials needed) -- 'from ddgs import DDGS' then "
    "'results = list(DDGS().text(query, max_results=3))'. Each result is a DICT, not an object -- "
    "access fields with 'result[\"title\"]' and 'result[\"body\"]', NEVER 'result.title' or "
    "'result.body' (attribute access on a dict raises AttributeError). A correct return line: "
    "'\"\\n\".join(f\"{r[\\'title\\']}: {r[\\'body\\']}\" for r in results)'. Never fake/stub a "
    "result -- that has been observed before to make the agent's final answer hallucinate "
    "stale/wrong info. Do NOT use the older 'duckduckgo_search' package -- deprecated, returns "
    "an empty list."
)

_TOOL_TYPE_INSTRUCTIONS = {
    "local_system_call": LOCAL_SYSTEM_CALL_INSTRUCTION,
    "no_auth_api": NO_AUTH_API_INSTRUCTION,
}


def ask_local_model_for_tools_code(
    task_description: str, tool_types: set, error_context: str = "", log=print
) -> str:
    system_instruction = _BASE_INSTRUCTION + "\n\n" + _STRUCTURE_INSTRUCTION
    for tool_type in sorted(tool_types):
        if tool_type in _TOOL_TYPE_INSTRUCTIONS:
            system_instruction += "\n\n" + _TOOL_TYPE_INSTRUCTIONS[tool_type]

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous version of {TOOLS_FILENAME} had this problem. Completely fix it:\n{error_context}"

    return _ask(system_instruction, f"{task_description}\n\nWrite {TOOLS_FILENAME}.", log)


# =====================================================================
# GENERATE -- ROUND 2: main.py (the agent loop). Grounded in the actual
# agent_tools.py just generated -- shown as real code, not re-described --
# so this round never redefines the tools, only imports and uses them.
# =====================================================================
def ask_local_model_for_agent_code(tools_code: str, error_context: str = "", log=print) -> str:
    system_instruction = (
        _BASE_INSTRUCTION + "\n\n"
        f"This script will be run non-interactively -- never call 'input()'. Write {AGENT_FILENAME}, "
        f"which imports from the ALREADY-EXISTING {TOOLS_FILENAME} shown below -- do not "
        "redefine TOOLS, TOOL_REGISTRY, or any tool function; only import and use them:\n"
        f"'from {TOOLS_FILENAME[:-3]} import TOOLS, TOOL_REGISTRY'\n\n"
        "Import the 'ollama' package with plain 'import ollama' -- never 'from ollama import "
        "ollama', which is not a valid import (ollama does not export a name called 'ollama' "
        "from itself) and has been observed before as a repeated ImportError.\n\n"
        "Define ask_agent(question, tools, tool_registry) -- tools and tool_registry are "
        "PARAMETERS, not read from module-level globals inside the function -- with this exact "
        "body shape:\n\n"
        "def ask_agent(question, tools, tool_registry):\n"
        "    messages = [{'role': 'user', 'content': question}]\n"
        f"    first = ollama.chat(model='{LOCAL_MODEL}', messages=messages, tools=tools)\n"
        "    reply = first['message']\n"
        "    tool_calls = reply.get('tool_calls')\n"
        "    if not tool_calls:\n"
        "        return reply['content']\n"
        "    messages.append(reply)\n"
        "    for call in tool_calls:\n"
        "        name = call['function']['name']\n"
        "        args = call['function']['arguments']\n"
        "        result = tool_registry[name](**args)\n"
        "        messages.append({'role': 'tool', 'content': str(result), 'name': name})\n"
        f"    second = ollama.chat(model='{LOCAL_MODEL}', messages=messages, tools=tools)\n"
        "    return second['message']['content']\n\n"
        "The LLM itself must decide which tool(s) to invoke via 'tool_calls' above -- never "
        "keyword-match the question yourself in plain Python to call a tool function directly; "
        "that defeats the point of the task.\n\n"
        "Under 'if __name__ == \"__main__\":', call ask_agent(question, TOOLS, TOOL_REGISTRY) "
        "with at least four different example questions, chosen so each one should naturally "
        "route to a different one of the four tools -- one question that happens to need every "
        "tool proves nothing about whether the model, rather than your code, made the choice."
    )

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous version of {AGENT_FILENAME} had this problem. Completely fix it:\n{error_context}"

    user_content = (
        f"The following {TOOLS_FILENAME} already exists and is correct -- import from it, do "
        f"not redefine anything in it:\n\n```python\n{tools_code}\n```"
    )
    return _ask(system_instruction, user_content, log)


# =====================================================================
# PARSE + SAVE
# =====================================================================
def parse_and_write_file(raw_llm_text: str, target_dir: str, filename: str) -> str:
    clean_text = re.sub(r"<think>.*?</think>", "", raw_llm_text, flags=re.DOTALL)
    os.makedirs(target_dir, exist_ok=True)

    code_match = re.search(r"```python\s*(.*?)\s*```", clean_text, re.DOTALL)
    clean_code = code_match.group(1).strip() if code_match else clean_text.strip()

    path = os.path.join(target_dir, filename)
    with open(path, "w") as f:
        f.write(clean_code)
    return path


# =====================================================================
# STATIC CHECK -- no execution, no model calls, no side effects beyond the
# .pyc py_compile itself writes. Purpose: catch a missing import or an
# invented/undefined name (e.g. `os.arch()`, `ddgs.DDGS()` with no `import
# ddgs`) instantly, before spending a live EXECUTE run -- and its slow
# CPU-bound Ollama inference calls -- discovering the same bug the hard way.
# =====================================================================
def _all_defined_names(tree: ast.AST) -> set:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def static_check(path: str) -> tuple[bool, str]:
    """Returns (passed, detail). Checks, in order: syntax (ast.parse), bytecode
    compile (py_compile), then a flat scan for any `name.attr(...)` or bare
    `name(...)` where `name` is never imported or defined anywhere in the file."""
    with open(path) as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        return False, f"Syntax error in {os.path.basename(path)}: {e}"

    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"Compile failed on {os.path.basename(path)}: {e}"

    defined = _all_defined_names(tree) | _BUILTIN_NAMES
    issues = []
    seen = set()
    for node in ast.walk(tree):
        # Every bare name LOAD, regardless of what it's used for -- X.attr(...), X(...),
        # X[...], or just X on its own. A narrower check that only looked at Attribute/Call
        # patterns missed TOOL_REGISTRY[name](...) (a Subscript), which is exactly how this
        # generated code's own dispatch pattern accesses it -- so this must be general, not
        # pattern-specific, or the one undefined name that matters most here slips through.
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in defined:
            if node.id not in seen:
                seen.add(node.id)
                issues.append(
                    f"'{node.id}' is used but never imported or defined anywhere in "
                    f"{os.path.basename(path)}."
                )

    if issues:
        return False, "\n".join(issues)
    return True, ""


# =====================================================================
# EXECUTE
# =====================================================================
def execute_in_sandbox(target_filename: str, cwd: str, timeout: float = 60, log=print):
    log(f"Running {target_filename}...")
    try:
        result = subprocess.run(
            [sys.executable, target_filename],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode, result.stderr, result.stdout
    except subprocess.TimeoutExpired:
        return -1, f"PROCESS_TIMEOUT: Script runtime exceeded maximum threshold ({timeout:.0f}s).", ""


# =====================================================================
# RUNTIME ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    print("====================================================")
    print("AI AGENT HARNESS (standalone experiment)")
    print(f"Model: {LOCAL_MODEL}")
    print("====================================================")

    task_description = define_task()
    tool_types = classify_tool_types(task_description)
    print(f"Tool types identified: {sorted(tool_types)}\n")

    max_attempts = 5
    tools_error_contexts = []
    agent_error_contexts = []
    # Every past attempt's error, not just the most recent -- a retry loop that only sees the
    # last error can fix that bug while silently regressing on an earlier one it can no longer
    # see (observed: attempt 3 re-introduced attempt 1's exact schema bug after attempt 2's
    # error, about a different bug, pushed it out of context).

    tools_path = None
    tools_code = None
    success = False

    for attempt in range(1, max_attempts + 1):
        attempt_dir = os.path.join(OUTPUT_ROOT, f"attempt{attempt}")
        os.makedirs(attempt_dir, exist_ok=True)
        log_path = os.path.join(attempt_dir, "run.log")

        def log(msg, _log_path=log_path):
            print(msg)
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(str(msg) + "\n")

        log(f"\n--- attempt {attempt}/{max_attempts} ---")

        # ROUND 1 (agent_tools.py) -- only regenerated while it hasn't yet passed static
        # check. Once it passes, it's cached and reused across remaining attempts, same as
        # code_harness.py's source_files caching -- a round-2-only failure shouldn't burn a
        # fresh round-1 generation too.
        if tools_path is None:
            combined_tools_errors = "\n\n---\n\n".join(
                f"Attempt {i + 1}:\n{err}" for i, err in enumerate(tools_error_contexts)
            )
            raw_tools_output = ask_local_model_for_tools_code(
                task_description, tool_types, error_context=combined_tools_errors, log=log
            )
            candidate_tools_path = parse_and_write_file(raw_tools_output, attempt_dir, filename=TOOLS_FILENAME)

            with open(candidate_tools_path) as f:
                candidate_tools_code = f.read()
            log(f"\n--- {TOOLS_FILENAME} ---\n{candidate_tools_code}")

            tools_check_passed, tools_check_detail = static_check(candidate_tools_path)
            if not tools_check_passed:
                log(f"\n{TOOLS_FILENAME} STATIC CHECK FAILED:\n{tools_check_detail}")
                tools_error_contexts.append(tools_check_detail)
                continue

            log(f"\n{TOOLS_FILENAME} STATIC CHECK PASSED.")
            tools_path, tools_code = candidate_tools_path, candidate_tools_code
        else:
            # Reuse the already-passing agent_tools.py in this attempt's own dir too, so
            # EXECUTE later finds both files side by side regardless of which attempt each
            # came from.
            reused_path = os.path.join(attempt_dir, TOOLS_FILENAME)
            shutil.copy(tools_path, reused_path)
            tools_path = reused_path
            log(f"\nReusing already-passing {TOOLS_FILENAME} from an earlier attempt.")

        # ROUND 2 (main.py) -- grounded in the real, already-checked agent_tools.py content.
        combined_agent_errors = "\n\n---\n\n".join(
            f"Attempt {i + 1}:\n{err}" for i, err in enumerate(agent_error_contexts)
        )
        raw_agent_output = ask_local_model_for_agent_code(
            tools_code, error_context=combined_agent_errors, log=log
        )
        path = parse_and_write_file(raw_agent_output, attempt_dir, filename=AGENT_FILENAME)

        with open(path) as f:
            log(f"\n--- {os.path.basename(path)} ---\n{f.read()}")

        check_passed, check_detail = static_check(path)

        if check_passed:
            log(f"\n{AGENT_FILENAME} STATIC CHECK PASSED on attempt {attempt} (kept in {attempt_dir}/)")
            success = True
            break
        else:
            log(f"\n{AGENT_FILENAME} STATIC CHECK FAILED:\n{check_detail}")
            agent_error_contexts.append(check_detail)

    if not success:
        print(f"\nFAILED: no attempt passed the static check within {max_attempts} tries.")
    else:
        answer = input(
            f"\nStatic check passed for {path} -- this has NOT been run yet (it makes real, "
            f"slow Ollama inference calls on this machine). Execute it now? [y/N]: "
        ).strip().lower()
        if answer == "y":
            exit_code, stderr, stdout = execute_in_sandbox(
                os.path.basename(path), cwd=attempt_dir, timeout=180, log=log
            )
            if exit_code == 0:
                log(f"\nEXECUTE SUCCESS.\nOutput:\n{stdout.strip()}")
            else:
                log(f"\nEXECUTE FAILED (exit {exit_code}):\n{stderr.strip()}")
        else:
            print(f"Skipped execution. Code is at {path} -- run it yourself whenever you're ready.")
