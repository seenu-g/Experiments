"""GENERATE stage: ask the model for code and parse its reply into file contents.

Parsing is decoupled from writing -- this module never touches disk. SAVE owns
that, so every attempt (pass or fail) can be persisted under a versioned name.
"""

import re

import ollama

from config import LOCAL_MODEL

FILE_HEADER_RE = re.compile(r"^#\s*===\s*FILE:\s*(?P<fname>\S+)\s*===\s*$", re.MULTILINE)
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


CONFIG_FORMAT_INSTRUCTION = (
    "Any config values (credentials, connection settings, etc.) must be stored in an INI file "
    "(e.g. db_config.ini), parsed via configparser -- never a Python dict, .env, or .json file. "
    "This keeps config storage consistent and in one predictable format across tasks."
)

AWS_INSTRUCTION = (
    "If the task involves AWS services via boto3, write production code with plain boto3 clients "
    "(no hardcoded endpoint_url). " + CONFIG_FORMAT_INSTRUCTION
)

AWS_TEST_INSTRUCTION = (
    "For the unit test file, mock AWS with moto: decorate test functions/classes with a bare "
    "@mock_aws (import via 'from moto import mock_aws'), and create boto3 clients/resources "
    "inside the mocked test using region_name='us-east-1' -- moto intercepts the calls in-process, "
    "so no real AWS credentials or network access are needed. mock_aws takes NO arguments -- never "
    "write @mock_aws('s3') or @mock_aws('ec2') or any other service name as an argument; that is "
    "the old, removed per-service API (mock_s3, mock_ec2, etc., which no longer exist in moto and "
    "will raise ImportError). The single, current @mock_aws decorator mocks every AWS service "
    "generically and takes no arguments at all. If the task's entrypoint is the test file, running "
    "it under moto must fully succeed without touching real AWS."
)


MYSQL_INSTRUCTION = (
    "If the task involves a MySQL database via mysql.connector, the config file's credential keys "
    "must be named exactly 'user' and 'password' (matching mysql.connector.connect()'s keyword "
    "arguments), never 'admin_username' or other names -- so the config section can be passed "
    "straight into connect(**config) without renaming keys. Always include both a 'user' key and a "
    "'password' key in the config file; never omit the password. " + CONFIG_FORMAT_INSTRUCTION
)

MYSQL_TEST_INSTRUCTION = (
    "Any test database or test user the code creates against a real MySQL server must have a name "
    "unique to that run -- suffix it with a timestamp (e.g. f'test_db_{int(time.time())}'), never a "
    "fixed literal like 'test_db'. This server persists between runs, so a fixed name collides with "
    "whatever a previous run's test left behind (e.g. it crashed before its own cleanup ran) with a "
    "'database exists' error that has nothing to do with whether this run's code is correct."
)


def build_system_instruction(
    error_context: str = "", external_system: str = "", needs_tests: bool = True
) -> str:
    system_instruction = (
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
        "Do not use this multi-file format unless the task genuinely requires more than one file.\n\n"
        + (
            "Include a test file that exercises the code."
            if needs_tests
            else "Do not write a test file -- only the production code the user asked for."
        )
    )

    if "aws" in external_system.lower():
        system_instruction += "\n\n" + AWS_INSTRUCTION
        if needs_tests:
            system_instruction += "\n\n" + AWS_TEST_INSTRUCTION

    if "mysql" in external_system.lower():
        system_instruction += "\n\n" + MYSQL_INSTRUCTION
        if needs_tests:
            system_instruction += "\n\n" + MYSQL_TEST_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous code failed. Completely fix this:\n{error_context}"

    return system_instruction


def ask_local_model_for_code(
    spec: str, error_context: str = "", external_system: str = "", needs_tests: bool = True
) -> str:
    system_instruction = build_system_instruction(error_context, external_system, needs_tests)

    print(f"Querying {LOCAL_MODEL}...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": spec},
        ],
        options={"temperature": 0.1},
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

        if ENTRY_MARKER_RE.search(block):
            entry_filename = fname
            block = ENTRY_MARKER_RE.sub("", block)

        files.append((fname, _strip_fence(block)))

    # A local-model repetition glitch can repeat the same "# === FILE: X ===" block
    # verbatim; collapse to one entry per filename (keeping the last occurrence,
    # same as save_attempt's overwrite-by-path behavior) so nothing downstream
    # writes/logs/checks the same file twice.
    files = list(dict(files).items())

    return files, entry_filename or files[-1][0]
