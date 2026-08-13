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
import subprocess
import sys
import time

import ollama

_BUILTIN_NAMES = set(dir(builtins))

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
# GENERATE
# =====================================================================
def ask_local_model_for_code(prompt: str, error_context: str = "", log=print) -> str:
    system_instruction = (
        "You are an expert Python software engineer. Your task is to output ONLY valid, "
        "executable Python code, with no conversational preamble, explanations, or commentary. "
        "Every 'import' statement required by any function, class, or standard-library call you use "
        "must be included at the top of its file. Never reference a module or name without importing it first.\n\n"
        "This script will be run non-interactively with no terminal attached. Never call 'input()' "
        "or otherwise wait on interactive/stdin input. Demonstrate the code with hardcoded example "
        "arguments under 'if __name__ == \"__main__\":'.\n\n"
        "Output exactly one ```python ... ``` block.\n\n"
        "The task requires tool-calling: the LLM itself must decide which tool(s) to invoke via "
        f"Ollama's 'tools' API -- do not keyword-match the user's question yourself in plain Python; "
        "that defeats the point of the task. Import the package with plain 'import ollama' at the "
        "top of the file, then call ollama.chat(...) -- never 'from ollama import ollama', which is "
        "not a valid import (ollama does not export a name called 'ollama' from itself) and has been "
        "observed before as a repeated ImportError that survived unchanged across retries even after "
        "being shown the exact traceback. Use the real 'ollama' package API "
        f"(model='{LOCAL_MODEL}'), never a placeholder-looking model name. Follow this exact shape, "
        "in this order -- do not invent your own control flow or reorder these pieces:\n\n"
        "1. TOOLS = [ ... ]  # one dict per tool, in EXACTLY this shape -- copy it, do not "
        "invent a different 'parameters' shape:\n"
        "   {\n"
        "       'type': 'function',\n"
        "       'function': {\n"
        "           'name': 'get_current_date_time',\n"
        "           'description': '...',\n"
        "           'parameters': {'type': 'object', 'properties': {}, 'required': []},\n"
        "       },\n"
        "   }\n"
        "   For a tool that takes an argument (e.g. web_search(query)), 'properties' is not empty:\n"
        "   'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', "
        "'description': '...'}}, 'required': ['query']}\n"
        "   'parameters' MUST always be a dict shaped exactly like the two examples above -- NEVER "
        "a bare list like [] or ['query']. A bare list has been observed before to fail with "
        "'pydantic_core.ValidationError: Input should be a valid dictionary', across multiple "
        "separate attempts, so double check this shape specifically before finishing.\n"
        "2. import platform and import psutil at the top of the file (both already installed) -- "
        "these exact two imports have been observed missing before even though get_system_info/"
        "get_running_processes below use them, causing NameError. Then define "
        "def get_current_date_time(): ..., def web_search(query): ..., "
        "def get_system_info(): ..., and def get_running_processes(): ...  -- the real tool "
        "functions, defined here, BEFORE the registry below. A dict literal evaluates immediately "
        "when the module loads, so referencing a function name in a dict before its own 'def' has "
        "run raises NameError -- this exact ordering mistake has been observed before, avoid it.\n"
        "   - web_search(query) must do a REAL search using the 'ddgs' package (already installed) -- "
        "'from ddgs import DDGS' then 'results = list(DDGS().text(query, max_results=3))', and "
        "return the results (e.g. join each result's 'title' and 'body'). Never fake, stub, or "
        "hardcode a placeholder search result -- a stubbed web_search has been observed before to "
        "make the agent's final answer hallucinate stale/wrong information instead of using real "
        "results. Do not use the older 'duckduckgo_search' package -- it is deprecated and its "
        "DDGS().text() call returns an empty result list; the real search functionality now lives "
        "in the 'ddgs' package under the same DDGS().text() method signature.\n"
        "   - get_system_info() must use the real 'psutil' and 'platform' packages (both already "
        "installed) -- e.g. platform.system(), platform.processor(), psutil.cpu_count(), "
        "psutil.virtual_memory(), psutil.disk_usage('/') -- and return a real summary string built "
        "from their actual return values. Never hardcode or fake any of these values.\n"
        "   - get_running_processes() must use the real 'psutil' package -- "
        "'for p in psutil.process_iter([\"pid\", \"name\"])' -- and return a real list/summary of "
        "actual running process names and PIDs. Cap it to a reasonable number (e.g. the first 10) "
        "so the result stays short. Never hardcode or fake a process list.\n"
        "3. TOOL_REGISTRY = {'get_current_date_time': get_current_date_time, 'web_search': web_search, "
        "'get_system_info': get_system_info, 'get_running_processes': get_running_processes}\n"
        "4. def ask_agent(question):\n"
        "       messages = [{'role': 'user', 'content': question}]\n"
        f"       first = ollama.chat(model='{LOCAL_MODEL}', messages=messages, tools=TOOLS)\n"
        "       reply = first['message']\n"
        "       tool_calls = reply.get('tool_calls')\n"
        "       if not tool_calls:\n"
        "           return reply['content']\n"
        "       messages.append(reply)\n"
        "       for call in tool_calls:\n"
        "           name = call['function']['name']\n"
        "           args = call['function']['arguments']\n"
        "           result = TOOL_REGISTRY[name](**args)\n"
        "           messages.append({'role': 'tool', 'content': str(result), 'name': name})\n"
        f"       second = ollama.chat(model='{LOCAL_MODEL}', messages=messages, tools=TOOLS)\n"
        "       return second['message']['content']\n\n"
        "5. Under 'if __name__ == \"__main__\":', call ask_agent() with at least four different "
        "example questions, chosen so each one should naturally route to a different one of the four "
        "tools -- one question that happens to need every tool proves nothing about whether the "
        "model, rather than your code, made the choice.\n\n"
        "Never call get_current_date_time(), web_search(), get_system_info(), or "
        "get_running_processes() directly from your own Python logic based on keywords found in the "
        "question -- the ONLY thing allowed to decide which tool(s) run is the 'tool_calls' the model "
        "returns from the first ollama.chat call."
    )

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous code had this problem. Completely fix it:\n{error_context}"

    log(f"Querying {LOCAL_MODEL}...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"]


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
        base_name = None
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load):
            base_name = node.value.id
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and isinstance(node.func.ctx, ast.Load):
            base_name = node.func.id

        if base_name is not None and base_name not in defined and base_name not in seen:
            seen.add(base_name)
            issues.append(
                f"'{base_name}' is used but never imported or defined anywhere in "
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

    max_attempts = 5
    error_contexts = []  # every past attempt's traceback, not just the most recent -- a retry
    # loop that only sees the last error can fix that bug while silently regressing on an
    # earlier one it can no longer see (observed: attempt 3 re-introduced attempt 1's exact
    # schema bug after attempt 2's traceback, about a different bug, pushed it out of context).
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

        combined_error_context = "\n\n---\n\n".join(
            f"Attempt {i + 1} failed with:\n{err}" for i, err in enumerate(error_contexts)
        )
        raw_output = ask_local_model_for_code(DEFAULT_TASK, error_context=combined_error_context, log=log)
        path = parse_and_write_file(raw_output, attempt_dir, filename="main.py")

        with open(path) as f:
            log(f"\n--- {os.path.basename(path)} ---\n{f.read()}")

        check_passed, check_detail = static_check(path)

        if check_passed:
            log(f"\nSTATIC CHECK PASSED on attempt {attempt} (kept in {attempt_dir}/)")
            success = True
            break
        else:
            log(f"\nSTATIC CHECK FAILED:\n{check_detail}")
            error_contexts.append(check_detail)

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
