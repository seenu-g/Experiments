"""Eval for parse_generated_files() in generate.py.

Regression check for the 2026-08-12 20260812_184645 run: the model replied
with FILE headers but no ```python fences, and put the ENTRYPOINT marker
mid-file (before `if __name__`) instead of right after the FILE header.
The old regex required both a fence and a header-adjacent ENTRYPOINT marker,
so it matched nothing and fell back to dumping the *entire* raw reply
(including the "# === FILE: db_config.ini ===" header and its
"[database]\nhost = ..." body) verbatim into one file -- which then failed
at runtime with `NameError: name 'database' is not defined` because
`[database]` isn't valid Python.

Run: python eval_generate.py
"""

import logging
import sys

from define import (
    _apply_external_system_override,
    _apply_needs_tests_override,
    extract_external_system,
    extract_needs_tests,
    extract_test_steps,
    strip_test_content,
)
from generate import (
    _format_source_code_context,
    build_source_system_instruction,
    build_test_system_instruction,
    parse_generated_files,
)

# Reconstructed verbatim from output/20260812_184645/run.log --
# no ```python fences, ENTRYPOINT marker sits mid-block.
UNFENCED_RAW = """# === FILE: db_config.ini ===
[database]
host = localhost
port = 3306
admin_username = admin_user
admin_password = admin_password

# === FILE: database_manager.py ===
import mysql.connector
from configparser import ConfigParser

config = ConfigParser()
config.read('db_config.ini')

def connect_to_db():
    return mysql.connector.connect(
        host=config['database']['host'],
        port=config['database']['port'],
        user=config['database']['admin_username'],
        password=config['database']['admin_password']
    )

# === FILE: test_database_manager.py ===
from database_manager import connect_to_db

def test_connect():
    assert connect_to_db() is not None

# === ENTRYPOINT ===
if __name__ == "__main__":
    test_connect()
"""

# The originally-documented format: fenced blocks, ENTRYPOINT right after
# the header. Must keep working after the fix.
FENCED_RAW = """# === FILE: validator.py ===
```python
def is_even(n):
    return n % 2 == 0
```

# === FILE: main.py ===
# === ENTRYPOINT ===
```python
from validator import is_even

if __name__ == "__main__":
    print(is_even(4))
```
"""

SINGLE_FILE_RAW = """```python
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(1, 2))
```
"""

# Reconstructed verbatim from output/20260812_211528/run.log -- the model's
# raw reply never opened a fence but ended with a lone, unpaired closing ```.
STRAY_CLOSING_FENCE_RAW = """import db_scripts

def test_database_and_user_creation_deletion():
    username = "admin"
    password = "password123"
    dbname = "testdb"

    db_scripts.create_database(username, password, dbname)

if __name__ == "__main__":
    test_database_and_user_creation_deletion()
```
"""


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_unfenced_with_midblock_entrypoint():
    files, entry = parse_generated_files(UNFENCED_RAW, default_filename="main.py")
    names = [f for f, _ in files]
    ok = True
    ok &= check("unfenced: 3 files parsed", names == ["db_config.ini", "database_manager.py", "test_database_manager.py"], f"got {names}")
    ok &= check("unfenced: entrypoint is test_database_manager.py", entry == "test_database_manager.py", f"got {entry}")

    ini_code = dict(files)["db_config.ini"]
    ok &= check("unfenced: db_config.ini has no leftover FILE markers", "=== FILE" not in ini_code, ini_code)
    ok &= check("unfenced: db_config.ini starts with [database]", ini_code.startswith("[database]"), ini_code[:40])

    mgr_code = dict(files)["database_manager.py"]
    ok &= check("unfenced: database_manager.py has no leftover FILE markers", "=== FILE" not in mgr_code, mgr_code[:80])
    ok &= check("unfenced: database_manager.py starts with its import", mgr_code.startswith("import mysql.connector"), mgr_code[:40])

    test_code = dict(files)["test_database_manager.py"]
    ok &= check("unfenced: ENTRYPOINT marker stripped from code", "ENTRYPOINT" not in test_code, test_code)
    ok &= check("unfenced: entry file still runs main guard", 'if __name__ == "__main__":' in test_code)
    return ok


def eval_fenced_backward_compat():
    files, entry = parse_generated_files(FENCED_RAW, default_filename="main.py")
    names = [f for f, _ in files]
    ok = True
    ok &= check("fenced: 2 files parsed", names == ["validator.py", "main.py"], f"got {names}")
    ok &= check("fenced: entrypoint is main.py", entry == "main.py", f"got {entry}")
    ok &= check("fenced: fences stripped from validator.py", "```" not in dict(files)["validator.py"])
    ok &= check("fenced: ENTRYPOINT marker stripped from main.py", "ENTRYPOINT" not in dict(files)["main.py"])
    return ok


def eval_single_file_fallback():
    files, entry = parse_generated_files(SINGLE_FILE_RAW, default_filename="main.py")
    ok = True
    ok &= check("single-file: one file named default", [f for f, _ in files] == ["main.py"])
    ok &= check("single-file: fence stripped", "```" not in dict(files)["main.py"])
    ok &= check("single-file: entrypoint is main.py", entry == "main.py")
    return ok


def eval_stray_closing_fence_stripped():
    files, entry = parse_generated_files(STRAY_CLOSING_FENCE_RAW, default_filename="main.py")
    code = dict(files)["main.py"]
    ok = True
    ok &= check("stray fence: no ``` left in saved code", "```" not in code, code)
    ok &= check(
        "stray fence: code still ends with the real last line",
        code.strip().endswith('test_database_and_user_creation_deletion()'),
        code[-80:],
    )
    ok &= check("stray fence: entrypoint is main.py", entry == "main.py")

    import ast

    try:
        ast.parse(code)
        parses = True
    except SyntaxError:
        parses = False
    ok &= check("stray fence: result is valid Python (ast.parse succeeds)", parses)
    return ok


def eval_duplicate_file_block_deduped():
    """Regression check for the 2026-08-12 20260812_230943 run (v2): the model's
    raw reply repeated the entire "# === FILE: test_db_manager.py ===" block
    verbatim (a local-LLM repetition glitch) -- before the fix, this doubled the
    file up in the returned `files` list, which then rippled into save_attempt
    writing it twice, the harness logging "Saved" twice, and RESOLVE analyzing
    the same file twice and reporting the same issue twice."""
    raw = """# === FILE: db_manager.py ===
```python
def create_database(db_name):
    pass
```

# === FILE: test_db_manager.py ===
# === ENTRYPOINT ===
```python
class TestDBManager:
    pass

if __name__ == "__main__":
    pass
```

# === FILE: test_db_manager.py ===
# === ENTRYPOINT ===
```python
class TestDBManager:
    pass

if __name__ == "__main__":
    pass
```
"""
    files, entry = parse_generated_files(raw, default_filename="main.py")
    names = [f for f, _ in files]
    ok = True
    ok &= check(
        "duplicate FILE block collapsed to one entry per filename",
        names == ["db_manager.py", "test_db_manager.py"],
        names,
    )
    ok &= check("entrypoint is still correctly identified", entry == "test_db_manager.py", entry)
    return ok


def eval_inline_entrypoint_annotation_on_file_header():
    """Regression check for the 2026-08-14 20260814_163031 run: the model wrote
    '# === FILE: ec2_manager.py (ENTRYPOINT) ===' -- folding the entrypoint marker
    onto the SAME line as the FILE header, instead of the instructed separate
    '# === ENTRYPOINT ===' line below it. The old FILE_HEADER_RE required the line
    to end immediately after '===', so this format deviation meant the header
    didn't match AT ALL -- the model's entire second file (real, correct code)
    silently got swallowed into the first file's content block, and the run's
    only saved file ended up named after the FIRST file (app_config.ini) with
    the second file's code appended inside it as literal text. Burned all 3
    retry attempts identically because the fed-back error ("Planned file
    'ec2_manager.py' was never generated") gave the model no reason to suspect
    its own header formatting was the actual cause."""
    raw = (
        "# === FILE: app_config.ini ===\n"
        "[aws_credentials]\n"
        "region = us-east-1\n"
        "\n"
        "# === FILE: ec2_manager.py (ENTRYPOINT) ===\n"
        "import boto3\n"
        "\n"
        "def create_instance():\n"
        "    pass\n"
    )
    files, entry = parse_generated_files(raw, default_filename="main.py")
    names = [f for f, _ in files]
    ok = True
    ok &= check(
        "both files parsed separately despite the inline (ENTRYPOINT) annotation",
        names == ["app_config.ini", "ec2_manager.py"],
        names,
    )
    ok &= check("entrypoint correctly identified as ec2_manager.py", entry == "ec2_manager.py", entry)
    ok &= check(
        "app_config.ini's content doesn't contain the second file's code",
        "boto3" not in dict(files)["app_config.ini"],
        dict(files)["app_config.ini"],
    )
    ok &= check(
        "the inline annotation text itself doesn't leak into ec2_manager.py's saved code",
        "ENTRYPOINT" not in dict(files)["ec2_manager.py"],
        dict(files)["ec2_manager.py"],
    )
    return ok


def eval_source_instruction_forbids_unrequested_command_dispatcher():
    """Regression check for the 2026-08-13 20260813_012157 run: the spec's Input
    line said 'User commands specifying the action...' (DEFINE's own paraphrase --
    the user never asked for a CLI), and GENERATE ran with it, inventing a
    parse_command/handle_command('ec2 my-instance create') dispatcher instead of
    plain create_ec2_instance(name)-style functions. The test file then called
    handle_command(...) without importing it, which RESOLVE correctly caught, but
    the real waste was GENERATE inventing an unrequested interface layer at all."""
    ok = True
    source = build_source_system_instruction()
    ok &= check(
        "source instruction requires one function per operation",
        "one function per" in source.lower(),
        source,
    )
    ok &= check(
        "source instruction forbids an unrequested command-string dispatcher",
        "handle_command" in source and "cli" in source.lower(),
        source,
    )
    return ok


def eval_source_instruction_forbids_writing_tests_when_fixing_a_test_failure():
    """Regression check for the 2026-08-13 20260813_162026 run: heap_sort's v1 production
    code was actually correct -- the real bug was a wrong expected value in the TEST round's
    own assertion (test_heapify expected a swap that shouldn't happen). EXECUTE failing resets
    BOTH rounds ('ambiguous which side is wrong'), so v2's source round got fed v1's test
    failure traceback as error_context -- and, despite being told 'no tests', got confused by
    being handed a test failure to 'fix' and wrote a test-shaped file itself
    (test_heap_sort_v2.py, calling heapify() without ever defining it), which RESOLVE
    correctly caught as a plain source-round failure. v3 repeated the same confusion. The run
    exhausted its retry budget without ever getting back to the v1 code that already worked."""
    ok = True
    source = build_source_system_instruction()
    ok &= check(
        "source instruction addresses being handed a test-failure error to 'fix'",
        "test assertion failure" in source.lower(),
        source,
    )
    ok &= check(
        "source instruction explicitly forbids writing test code in that situation",
        "do not write any test code" in source.lower() or "do not write any test" in source.lower(),
        source,
    )
    ok &= check(
        "source instruction tells the model its logic is likely already correct in that case",
        "already correct" in source.lower(),
        source,
    )
    return ok


def eval_test_instruction_requires_test_file_to_run_its_tests():
    """Regression check for the 2026-08-13 20260813_012157 run: ec2_manager_test_v2.py
    defined 6 @mock_aws test_*() functions but never called any of them -- no
    unittest.main(), no 'if __name__' block invoking them at all. EXECUTE ran it as
    a plain script, which just defines the functions and exits 0 having tested
    nothing, and the harness logged 'SUCCESS on v2' for code that was never
    actually exercised. The old instruction only said to 'include a test file',
    never that it must actually run its tests and fail non-zero on a failure."""
    ok = True
    test_instruction = build_test_system_instruction()
    ok &= check(
        "instruction requires the test file to actually run its tests",
        "tested nothing" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction covers the unittest.TestCase case (unittest.main())",
        "unittest.main()" in test_instruction,
        test_instruction,
    )
    ok &= check(
        "instruction covers the bare test_*() function case too",
        "test_*()" in test_instruction,
        test_instruction,
    )
    return ok


def eval_format_source_code_context():
    """The test-writing call's user message must ground it in the actual saved
    source files, not a paraphrase -- given a files list, the rendered block
    must contain each filename's own FILE header and its exact code content."""
    source_files = [
        ("ec2_manager.py", "def create_ec2_instance(name):\n    pass\n"),
        ("db_config.ini", "[DEFAULT]\nregion = us-east-1\n"),
    ]
    rendered = _format_source_code_context(source_files)
    ok = True
    ok &= check(
        "rendered block contains each filename's own FILE header",
        "# === FILE: ec2_manager.py ===" in rendered and "# === FILE: db_config.ini ===" in rendered,
        rendered,
    )
    ok &= check(
        "rendered block contains each file's exact code content",
        "def create_ec2_instance(name):" in rendered and "region = us-east-1" in rendered,
        rendered,
    )
    return ok


def eval_apply_needs_tests_override():
    """Regression check for the 2026-08-13 20260813_013836 run: the raw prompt
    ('Write program that helps to manage EC2 instances... All actions done needs
    to be saved in log file...') never mentions tests anywhere, yet DEFINE's spec
    came back with 'Tests needed: Yes' -- GENERATE then spent ~10 minutes writing
    two unrequested test files nobody asked for. The same 20260813_012157 run had
    the identical problem."""
    logger = logging.getLogger("eval_generate_null")
    logger.addHandler(logging.NullHandler())

    raw_no_tests = (
        "Write program that helps to manage EC2 instances(create, delete, get all, get). "
        "S3 instances(create, delete, get all, get). All actions done needs to be saved "
        "in log file(Resource, Name of instance, Operation performed, Date and time)."
    )
    spec_saying_yes = (
        "Input: User commands specifying the action.\n\nOutput: Confirmation message.\n\n"
        "Steps:\n1. Perform the action.\n\n"
        "External System called: AWS\n\nTests needed: Yes"
    )

    ok = True

    corrected = _apply_needs_tests_override(spec_saying_yes, raw_no_tests, logger)
    ok &= check(
        "override corrects 'Yes' to 'No' when the description never mentions testing",
        extract_needs_tests(corrected) is False,
        corrected,
    )
    ok &= check(
        "override doesn't touch the rest of the spec",
        "Confirmation message" in corrected and "External System called: AWS" in corrected,
        corrected,
    )

    raw_with_tests = raw_no_tests + " Please write unit tests for each function."
    unchanged = _apply_needs_tests_override(spec_saying_yes, raw_with_tests, logger)
    ok &= check(
        "override is a no-op when the description does mention tests and spec already says Yes",
        unchanged == spec_saying_yes,
        unchanged,
    )

    spec_saying_no = spec_saying_yes.replace("Tests needed: Yes", "Tests needed: No")
    under_corrected = _apply_needs_tests_override(spec_saying_no, raw_with_tests, logger)
    ok &= check(
        "override also corrects 'No' to 'Yes' when the description does ask for tests",
        extract_needs_tests(under_corrected) is True,
        under_corrected,
    )

    return ok


def eval_extract_needs_tests():
    ok = True
    ok &= check(
        "extracts Yes",
        extract_needs_tests("Steps:\n1. Do a thing\n\nTests needed: Yes") is True,
    )
    ok &= check(
        "extracts No",
        extract_needs_tests("Steps:\n1. Do a thing\n\nTests needed: No") is False,
    )
    ok &= check(
        "defaults to True (old behavior) when field missing",
        extract_needs_tests("Input: None\nOutput: something\nSteps: do it") is True,
    )
    return ok


def eval_extract_test_steps_and_strip_test_content():
    """Regression check for the 2026-08-13 20260813_113104 run: the source round wrote a
    full test file itself (with its own missing 'import mysql.connector' bug) because the
    spec's Steps section named a test script -- a concrete instruction in the source round's
    own user message beat its system prompt's abstract 'do not write tests' rule. The fix
    splits the spec instead of arguing with the model about it: strip_test_content() removes
    all test content for the source round's prompt; extract_test_steps() pulls just the test
    content for the test round's prompt. Neither round's input should contain both halves."""
    spec = (
        "Input: None\n\n"
        "Output: Config file with database credentials, a manager script, and a test script.\n\n"
        "Steps:\n"
        "1. Create a configuration file named db_config.ini.\n"
        "2. Write database_manager.py with create/delete functions.\n\n"
        "Test Steps:\n"
        "1. Create a test database and user.\n"
        "2. Verify creation succeeded, then delete both.\n\n"
        "External System called: MySQL database\n\n"
        "Tests needed: Yes"
    )

    ok = True

    test_steps = extract_test_steps(spec)
    ok &= check(
        "extract_test_steps pulls only the Test Steps section's content",
        "test database and user" in test_steps and "Verify creation succeeded" in test_steps,
        test_steps,
    )
    ok &= check(
        "extract_test_steps doesn't leak the production Steps section",
        "database_manager.py" not in test_steps,
        test_steps,
    )
    ok &= check(
        "extract_test_steps defaults to a generic fallback when the field is missing",
        extract_test_steps("Input: None\nOutput: x\nSteps: do it") != "",
    )

    source_spec = strip_test_content(spec)
    ok &= check(
        "strip_test_content removes the Test Steps section entirely",
        "Test Steps:" not in source_spec and "test database and user" not in source_spec,
        source_spec,
    )
    ok &= check(
        "strip_test_content removes the Tests needed line entirely",
        "Tests needed:" not in source_spec,
        source_spec,
    )
    ok &= check(
        "strip_test_content keeps the production Steps section intact",
        "database_manager.py" in source_spec and "External System called: MySQL database" in source_spec,
        source_spec,
    )

    return ok


def eval_apply_external_system_override():
    """Regression check for the 2026-08-12 20260812_220825 run: the user's prompt
    opened with "mySQL database is on the machine", but DEFINE's spec came back
    with 'External System called: None'. GENERATE never got MYSQL_INSTRUCTION as
    a result, and the model used sqlite3/psycopg2 across three attempts instead
    of mysql.connector -- never once the right driver."""
    logger = logging.getLogger("eval_generate_null")
    logger.addHandler(logging.NullHandler())

    raw_description = (
        "mySQL database is on the machine 1. Write config to collect database "
        "credentials(user and password) 2. using credentials write code to create "
        "database, delete datavased and create user, delete user with admin access "
        "only for that database 3. write test unit client to see both operations work."
    )
    spec_saying_none = (
        "Input: None\n\nOutput: Config file with database credentials.\n\n"
        "Steps:\n1. Create a configuration file.\n\n"
        "External System called: None\n\nTests needed: Yes"
    )

    ok = True

    corrected = _apply_external_system_override(spec_saying_none, raw_description, logger)
    ok &= check(
        "override corrects 'None' to 'MySQL' when raw description names it",
        extract_external_system(corrected) == "MySQL",
        extract_external_system(corrected),
    )
    ok &= check(
        "override doesn't touch the rest of the spec",
        "Config file with database credentials" in corrected and "Tests needed: Yes" in corrected,
    )

    already_correct_spec = spec_saying_none.replace("External System called: None", "External System called: MySQL Database")
    unchanged = _apply_external_system_override(already_correct_spec, raw_description, logger)
    ok &= check(
        "override is a no-op when the spec already names the right system",
        unchanged == already_correct_spec,
    )

    unrelated_raw = "Write a function that sorts a list of numbers."
    unrelated_spec = spec_saying_none  # says None
    unchanged2 = _apply_external_system_override(unrelated_spec, unrelated_raw, logger)
    ok &= check(
        "override doesn't invent a system when the raw description has no known keyword",
        unchanged2 == unrelated_spec,
    )

    aws_raw = "Write a Lambda function that reads from an AWS S3 bucket."
    aws_corrected = _apply_external_system_override(spec_saying_none, aws_raw, logger)
    ok &= check(
        "override also works for AWS",
        extract_external_system(aws_corrected) == "AWS",
        extract_external_system(aws_corrected),
    )

    # Regression check for the 2026-08-12 20260812_233842 run: the prompt named
    # AWS services (EC2, S3) but never said the word "AWS" itself -- the old
    # keyword list only matched \baws\b and missed this entirely.
    ec2_s3_raw = (
        "Write program that helps to manage EC2 instances(create, delete, get all, get one), "
        "S3 instances(create, delete). All actions done needs to be saved in log file."
    )
    ec2_s3_corrected = _apply_external_system_override(spec_saying_none, ec2_s3_raw, logger)
    ok &= check(
        "override recognizes AWS from service names alone (EC2, S3), no literal 'AWS' needed",
        extract_external_system(ec2_s3_corrected) == "AWS",
        extract_external_system(ec2_s3_corrected),
    )

    lambda_raw = "Write a lambda function that takes a number and returns its square."
    lambda_unchanged = _apply_external_system_override(spec_saying_none, lambda_raw, logger)
    ok &= check(
        "bare 'lambda' (Python keyword) doesn't falsely trigger an AWS override",
        lambda_unchanged == spec_saying_none,
        extract_external_system(lambda_unchanged),
    )

    # Regression check for the 2026-08-13 20260813_182223 run: the raw prompt
    # said "uses a local LLM with tool-calling" and also needed MySQL. The old
    # override *replaced* the whole field, so if it had matched "Ollama" it
    # would have silently thrown away an already-correct "MySQL database,
    # internet" classification. The override must be additive.
    mysql_and_llm_raw = (
        "Write a program that uses a local LLM with tool-calling to answer questions "
        "using three tools: getting the current date/time, performing a web search, "
        "and querying a MySQL database."
    )
    spec_saying_mysql_internet = (
        "Input: A question.\n\nOutput: An answer.\n\nSteps:\n1. Answer it.\n\n"
        "External System called: MySQL database, internet\n\nTests needed: No"
    )
    additive_corrected = _apply_external_system_override(spec_saying_mysql_internet, mysql_and_llm_raw, logger)
    additive_value = extract_external_system(additive_corrected)
    ok &= check(
        "override ADDS 'Ollama' rather than replacing the already-correct MySQL/internet classification",
        "mysql" in additive_value.lower() and "ollama" in additive_value.lower(),
        additive_value,
    )

    # Mentions both "langchain" and "Ollama" -- both should match (additive), not just one.
    langchain_raw = "Write a program using langchain that connects to a local Ollama model."
    langchain_corrected = _apply_external_system_override(spec_saying_none, langchain_raw, logger)
    langchain_value = extract_external_system(langchain_corrected)
    ok &= check(
        "override recognizes LangChain (and Ollama, since the raw text names both)",
        "langchain" in langchain_value.lower() and "ollama" in langchain_value.lower(),
        langchain_value,
    )

    ollama_raw = "Write a Python program that sends a prompt to a local Ollama model."
    ollama_corrected = _apply_external_system_override(spec_saying_none, ollama_raw, logger)
    ok &= check(
        "override recognizes bare 'ollama'",
        extract_external_system(ollama_corrected) == "Ollama",
        extract_external_system(ollama_corrected),
    )

    local_llm_raw = "Write a program that uses a local LLM with tool-calling."
    local_llm_corrected = _apply_external_system_override(spec_saying_none, local_llm_raw, logger)
    ok &= check(
        "override recognizes 'local llm'/'tool-calling' even when 'ollama' is never said literally",
        extract_external_system(local_llm_corrected) == "Ollama",
        extract_external_system(local_llm_corrected),
    )

    return ok


def eval_extract_external_system():
    ok = True
    ok &= check(
        "extracts MySQL",
        extract_external_system("Steps:\n1. Do a thing\n\nExternal System called: MySQL Database") == "MySQL Database",
    )
    ok &= check(
        "extracts AWS",
        extract_external_system("External System called: AWS (S3, DynamoDB)") == "AWS (S3, DynamoDB)",
    )
    ok &= check(
        "defaults to None when field missing",
        extract_external_system("Input: None\nOutput: something\nSteps: do it") == "None",
    )
    return ok


if __name__ == "__main__":
    results = [
        eval_unfenced_with_midblock_entrypoint(),
        eval_fenced_backward_compat(),
        eval_single_file_fallback(),
        eval_stray_closing_fence_stripped(),
        eval_duplicate_file_block_deduped(),
        eval_inline_entrypoint_annotation_on_file_header(),
        eval_source_instruction_forbids_unrequested_command_dispatcher(),
        eval_source_instruction_forbids_writing_tests_when_fixing_a_test_failure(),
        eval_test_instruction_requires_test_file_to_run_its_tests(),
        eval_format_source_code_context(),
        eval_apply_external_system_override(),
        eval_apply_needs_tests_override(),
        eval_extract_external_system(),
        eval_extract_needs_tests(),
        eval_extract_test_steps_and_strip_test_content(),
    ]
    sys.exit(0 if all(results) else 1)
