"""GENERATE stage: ask the model for code and parse its reply into file contents.

Two ordered calls per attempt -- source code first, then test code grounded in
the actual saved source content -- so the test-writing call is never guessing
at what the source code looks like. See build_source_system_instruction() and
build_test_system_instruction() below.

Parsing is decoupled from writing -- this module never touches disk. SAVE owns
that, so every attempt (pass or fail) can be persisted under a versioned name.
"""

import re

import ollama

from config import LOCAL_MODEL, OLLAMA_KEEP_ALIVE
from systems import ALL_SYSTEMS

FILE_HEADER_RE = re.compile(
    r"^#\s*===\s*FILE:\s*(?P<fname>\S+)(?P<inline_entry>\s*\((?i:ENTRYPOINT)\))?\s*===\s*$",
    re.MULTILINE,
)
ENTRY_MARKER_RE = re.compile(r"^[ \t]*#\s*===\s*ENTRYPOINT\s*===\s*$\n?", re.MULTILINE)
FENCE_RE = re.compile(r"```\w*\s*\n?(?P<code>.*?)```", re.DOTALL)
STRAY_FENCE_LINE_RE = re.compile(r"^```\w*\s*$")


def _strip_fence(block: str) -> str:
    """Return the code inside a ```...``` fence if present, else the block as-is,
    with any leftover unpaired fence marker line trimmed from the edges.

    The model doesn't always fence its code despite instructions, and when it
    does, the open/close pair doesn't always both show up (e.g. a lone closing
    ``` with no opener) -- FENCE_RE only strips a matched pair, so a stray
    ``` line surviving on its own would otherwise get saved as part of the
    code and break ast.parse.
    """
    fence_match = FENCE_RE.search(block)
    code = fence_match.group("code").strip() if fence_match else block.strip()

    lines = code.split("\n")
    while lines and STRAY_FENCE_LINE_RE.match(lines[0]):
        lines.pop(0)
    while lines and STRAY_FENCE_LINE_RE.match(lines[-1]):
        lines.pop()
    return "\n".join(lines).strip()


_BASE_INSTRUCTION = (
    "You are an expert Python software engineer. Your task is to output ONLY valid, "
    "executable Python code, with no conversational preamble, explanations, or commentary. "
    "Every 'import' statement required by any function, class, or standard-library call you use "
    "must be included at the top of its file. Never reference a module or name without importing it first.\n\n"
    "This script will be run non-interactively with no terminal attached. Never call 'input()' "
    "or otherwise wait on interactive/stdin input. Demonstrate the code with hardcoded example "
    "arguments under 'if __name__ == \"__main__\":'.\n\n"
    "If the task can be done in a single file, output exactly one ```python ... ``` block.\n\n"
    "If the task explicitly requires multiple files (e.g. one module imported by another), output "
    "one ```python ... ``` block per file, and immediately BEFORE each block put a line in exactly "
    "this form:\n"
    "# === FILE: <filename.py> ===\n"
    "All files you output will be saved together in the same folder, so a plain "
    "'import <filename_without_.py>' between them will resolve correctly. Put the file that should "
    "be run directly (the one with 'if __name__ == \"__main__\":') LAST, and mark the line right "
    "after its FILE header with:\n"
    "# === ENTRYPOINT ===\n"
    "Do not use this multi-file format unless the task genuinely requires more than one file."
)

_SOURCE_ONLY_INSTRUCTION = (
    "Write only production code here -- do not write any test file, test function, or test class; "
    "a separate call handles tests. Expose one function per distinct operation the task describes "
    "(e.g. create_x(...), delete_x(...), get_x(...)), and call those functions directly from the "
    "__main__ example. Do not invent a single dispatcher function that parses a command string "
    "(e.g. handle_command('ec2 my-instance create')) to route between operations unless the task "
    "explicitly asks for a CLI or command-line interface -- an unrequested parsing layer is code a "
    "later test round then also has to exercise indirectly, for no benefit. If the error you're "
    "fixing is a test assertion failure (e.g. 'AssertionError: Lists differ', a unittest FAIL "
    "block) rather than a Python exception raised by your own code, that means your production "
    "logic is likely already correct and the test itself was wrong -- do NOT write any test code "
    "here in response to it; resubmit your logic unchanged unless you can identify an actual "
    "defect in it."
)

_TEST_ONLY_INSTRUCTION = (
    "Write only the test file(s) here. The production code shown to you below in the user message "
    "already exists, has already passed lint/resolve/compile checks, and is correct -- import from "
    "it, do not redefine, rewrite, or duplicate any function, class, or file already shown to you. "
    "The test file must actually RUN its own tests when executed directly and exit with a non-zero "
    "code if any test fails -- a test file that only defines test functions/classes but never "
    "invokes them will exit 0 having tested nothing, which is worse than no test file at all. If it "
    "uses unittest.TestCase, put 'unittest.main()' under 'if __name__ == \"__main__\":'. If it uses "
    "bare test_*() functions instead (no unittest), call every one of them under 'if __name__ == "
    '"__main__":\' so a failing assertion raises and the process exits non-zero.'
)


def build_source_system_instruction(error_context: str = "", external_system: str = "") -> str:
    system_instruction = _BASE_INSTRUCTION + "\n\n" + _SOURCE_ONLY_INSTRUCTION

    for system in ALL_SYSTEMS:
        if system.matches(external_system):
            system_instruction += "\n\n" + system.SOURCE_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous code failed. Completely fix this:\n{error_context}"

    return system_instruction


def build_test_system_instruction(error_context: str = "", external_system: str = "") -> str:
    system_instruction = _BASE_INSTRUCTION + "\n\n" + _TEST_ONLY_INSTRUCTION

    for system in ALL_SYSTEMS:
        if system.matches(external_system) and system.TEST_INSTRUCTION:
            system_instruction += "\n\n" + system.TEST_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous test code failed. Completely fix this:\n{error_context}"

    return system_instruction


def _format_plan_context(planned_files: list | None) -> str:
    """Render the confirmed PLAN-stage manifest (see plan.py) as context so
    GENERATE produces exactly the files/functions the user already confirmed,
    not a fresh, silent re-invention of file/function structure on every call.
    Returns "" when there's no plan (e.g. no PLAN stage ran) -- callers append
    this, so an empty string is a clean no-op."""
    if not planned_files:
        return ""

    lines = []
    for planned in planned_files:
        functions = ", ".join(planned["functions"]) if planned["functions"] else "N/A"
        entrypoint = " (ENTRYPOINT)" if planned["entrypoint"] else ""
        lines.append(f"- {planned['filename']}{entrypoint}: {planned['purpose']} -- functions: {functions}")

    return (
        "\n\nProduce exactly these files, in this order, with these top-level functions/classes "
        "-- you may add private helpers, but do not omit, rename, or add top-level files beyond "
        "this plan without reason:\n" + "\n".join(lines)
    )


def _format_source_code_context(source_files: list) -> str:
    """Render the actual saved source files as context for the test-writing call,
    so it's grounded in what really exists instead of guessing at it."""
    blocks = []
    for filename, code in source_files:
        blocks.append(
            f"# === FILE: {filename} ===\n"
            f"# This file already exists and is correct -- import from it, do not rewrite it.\n"
            f"{code}"
        )
    return "\n\n".join(blocks)


def ask_local_model_for_source_code(
    source_spec: str,
    error_context: str = "",
    external_system: str = "",
    planned_files: list | None = None,
) -> str:
    """`source_spec` is expected to already have any test-writing content stripped out by the
    caller (see define.strip_test_content) -- this round's user message should describe
    nothing about tests at all, not even a step to ignore.

    `planned_files`: the source-round subset of the confirmed PLAN-stage manifest (see plan.py),
    already filtered by the caller (is_test=False). None when no PLAN stage ran."""
    system_instruction = build_source_system_instruction(error_context, external_system)
    user_content = source_spec + _format_plan_context(planned_files)

    print(f"Querying {LOCAL_MODEL} (source)...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
        options={"temperature": 0.1},
        keep_alive=OLLAMA_KEEP_ALIVE,
    )
    return response["message"]["content"]


def ask_local_model_for_test_code(
    test_spec: str,
    source_files: list,
    error_context: str = "",
    external_system: str = "",
    planned_files: list | None = None,
) -> str:
    """`test_spec` is expected to be just the spec's test-related content (see
    define.extract_test_steps), not the full original spec -- this round is grounded in the
    real source code below, not a repeat of the production Input/Output/Steps it never needs.

    `planned_files`: the test-round subset of the confirmed PLAN-stage manifest (see plan.py),
    already filtered by the caller (is_test=True). None when no PLAN stage ran."""
    system_instruction = build_test_system_instruction(error_context, external_system)
    user_content = (
        f"{test_spec}\n\n"
        "The following production code already exists and has already passed "
        "lint/resolve/compile -- write test(s) against it exactly as shown, do not redefine "
        "any of it:\n\n"
        f"{_format_source_code_context(source_files)}"
        f"{_format_plan_context(planned_files)}"
    )

    print(f"Querying {LOCAL_MODEL} (test)...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
        options={"temperature": 0.1},
        keep_alive=OLLAMA_KEEP_ALIVE,
    )
    return response["message"]["content"]


def parse_generated_files(raw_llm_text: str, default_filename: str) -> tuple[list, str]:
    """Extract file(s) from the model's reply.

    Returns (files, entry_filename) where files is a list of (filename, code) tuples
    and entry_filename names which of those should be executed. Nothing is written
    to disk here -- SAVE does that with version-numbered filenames.
    """
    clean_text = re.sub(r"<think>.*?</think>", "", raw_llm_text, flags=re.DOTALL)

    headers = list(FILE_HEADER_RE.finditer(clean_text))

    if not headers:
        code = ENTRY_MARKER_RE.sub("", clean_text)
        return [(default_filename, _strip_fence(code))], default_filename

    files = []
    entry_filename = None
    for i, header in enumerate(headers):
        fname = header.group("fname")
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(clean_text)
        block = clean_text[start:end]

        # Two ways the model marks the entrypoint: a standalone "# === ENTRYPOINT ===" line
        # in the body (the instructed format), or "(ENTRYPOINT)" folded inline onto the FILE
        # header itself (a format deviation observed in real output -- the strict old regex
        # failed to match that header line at all, silently merging this file's entire content
        # into the PRECEDING file's block; see the 20260814_163031 run).
        if header.group("inline_entry") or ENTRY_MARKER_RE.search(block):
            entry_filename = fname
            block = ENTRY_MARKER_RE.sub("", block)

        files.append((fname, _strip_fence(block)))

    # A local-model repetition glitch can repeat the same "# === FILE: X ===" block
    # verbatim; collapse to one entry per filename (keeping the last occurrence,
    # same as save_attempt's overwrite-by-path behavior) so nothing downstream
    # writes/logs/checks the same file twice.
    files = list(dict(files).items())

    return files, entry_filename or files[-1][0]
