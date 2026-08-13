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
    "Any config values (credentials, connection settings, etc.) must be stored in ONE INI file "
    "(e.g. app_config.ini) shared by whatever external systems the task involves -- AWS "
    "credentials/region and a database's credentials both belong in that same file if a task "
    "needs both, never split across separate config files. Parse it via configparser -- never a "
    "Python dict, .env, or .json file. This keeps config storage consistent and in one "
    "predictable format across tasks. If any file calls configparser's .read('app_config.ini') "
    "(or whatever you name it), that exact .ini file MUST itself be one of the files you output, "
    "with its own '# === FILE: app_config.ini ===' header and fenced block -- referencing a "
    "config file without actually outputting it is a bug: configparser.read() does not raise an "
    "error for a missing file, it silently does nothing, so the code only fails later with a "
    "confusing KeyError when a key is looked up."
)

AWS_INSTRUCTION = (
    "If the task involves AWS services via boto3, write production code with plain boto3 clients "
    "(no hardcoded endpoint_url). Store the AWS region AND credentials in the same config INI "
    "file, under keys named exactly 'region', 'aws_access_key_id', and 'aws_secret_access_key' "
    "(e.g. 'region = us-east-1', 'aws_access_key_id = your_access_key', 'aws_secret_access_key = "
    "your_secret_key' in the same section) -- the actual values are placeholders a human fills in "
    "later, but the KEYS must exist. Every boto3.client(...)/boto3.resource(...) call must pass "
    "all three explicitly -- region_name=<config value>, aws_access_key_id=<config value>, "
    "aws_secret_access_key=<config value> -- read from the config, never hardcoded directly in "
    "the boto3 call itself and never omitted. Do not rely on any of these being available some "
    "other way (environment variables, ~/.aws/config, an IAM role): there is no default region or "
    "credentials configured in this environment, so boto3 raises NoRegionError/NoCredentialsError "
    "before a call even reaches AWS (or moto, under test) if any of the three is omitted. "
    + CONFIG_FORMAT_INSTRUCTION
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
    "it under moto must fully succeed without touching real AWS. Each test must be self-contained: "
    "create every resource that test needs within that same test (never assume a resource created "
    "by a different test still exists -- test order is not guaranteed and each test may run against "
    "a fresh mock), and only ever delete/terminate a resource that this same test created -- never "
    "delete or terminate a resource you did not create yourself, even inside the mock. Every "
    "resource name/ID a test creates (bucket name, instance name, etc.) must be unique to that "
    "test -- pass it in as a variable built from a timestamp (e.g. f'test-bucket-{int(time.time())}'), "
    "never a fixed literal like 'test-bucket' reused across multiple test methods, so tests can "
    "never collide on the same resource name. If you use time.time() for this, the test file must "
    "'import time' at the top -- it is not implicitly available just because it's used elsewhere."
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

    if "aws" in external_system.lower():
        system_instruction += "\n\n" + AWS_INSTRUCTION

    if "mysql" in external_system.lower():
        system_instruction += "\n\n" + MYSQL_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous code failed. Completely fix this:\n{error_context}"

    return system_instruction


def build_test_system_instruction(error_context: str = "", external_system: str = "") -> str:
    system_instruction = _BASE_INSTRUCTION + "\n\n" + _TEST_ONLY_INSTRUCTION

    if "aws" in external_system.lower():
        system_instruction += "\n\n" + AWS_TEST_INSTRUCTION

    if "mysql" in external_system.lower():
        system_instruction += "\n\n" + MYSQL_TEST_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous test code failed. Completely fix this:\n{error_context}"

    return system_instruction


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
    source_spec: str, error_context: str = "", external_system: str = ""
) -> str:
    """`source_spec` is expected to already have any test-writing content stripped out by the
    caller (see define.strip_test_content) -- this round's user message should describe
    nothing about tests at all, not even a step to ignore."""
    system_instruction = build_source_system_instruction(error_context, external_system)

    print(f"Querying {LOCAL_MODEL} (source)...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": source_spec},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"]


def ask_local_model_for_test_code(
    test_spec: str, source_files: list, error_context: str = "", external_system: str = ""
) -> str:
    """`test_spec` is expected to be just the spec's test-related content (see
    define.extract_test_steps), not the full original spec -- this round is grounded in the
    real source code below, not a repeat of the production Input/Output/Steps it never needs."""
    system_instruction = build_test_system_instruction(error_context, external_system)
    user_content = (
        f"{test_spec}\n\n"
        "The following production code already exists and has already passed "
        "lint/resolve/compile -- write test(s) against it exactly as shown, do not redefine "
        "any of it:\n\n"
        f"{_format_source_code_context(source_files)}"
    )

    print(f"Querying {LOCAL_MODEL} (test)...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
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
