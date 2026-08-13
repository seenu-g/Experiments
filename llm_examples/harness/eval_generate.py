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
    AWS_INSTRUCTION,
    AWS_TEST_INSTRUCTION,
    MYSQL_INSTRUCTION,
    MYSQL_TEST_INSTRUCTION,
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


def eval_external_system_gates_aws_instruction():
    ok = True
    ok &= check(
        "AWS block included when external_system=AWS",
        AWS_INSTRUCTION in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS block excluded when external_system=MySQL",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "AWS block excluded when external_system=None",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system="None"),
    )
    ok &= check(
        "AWS block excluded when external_system=''",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system=""),
    )
    ok &= check(
        "MySQL block included when external_system=MySQL Database",
        MYSQL_INSTRUCTION in build_source_system_instruction(external_system="MySQL Database"),
    )
    ok &= check(
        "MySQL block excluded when external_system=AWS",
        MYSQL_INSTRUCTION not in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS block excluded when external_system=MySQL Database",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system="MySQL Database"),
    )
    return ok


def eval_config_format_instruction_requires_ini_file_to_be_output():
    """Regression check for the 2026-08-13 20260813_013836 run (v3): ec2_manager.py
    and s3_manager.py both called config.read('db_config.ini'), but the model never
    once included a FILE block for db_config.ini itself across all 3 attempts.
    configparser.read() silently no-ops on a missing file, so this only surfaced as
    'KeyError: region' deep in EXECUTE. CONFIG_FORMAT_INSTRUCTION said to use an INI
    file but never said the model must actually output it as one of its files --
    this applies to both AWS and MySQL since both compose CONFIG_FORMAT_INSTRUCTION."""
    ok = True
    aws = build_source_system_instruction(external_system="AWS")
    ok &= check(
        "AWS prompt requires the .ini file to be one of the output FILE blocks",
        "FILE: app_config.ini" in aws and "MUST itself be one of the files you output" in aws,
        aws,
    )
    mysql = build_source_system_instruction(external_system="MySQL Database")
    ok &= check(
        "MySQL prompt requires the .ini file to be one of the output FILE blocks too",
        "MUST itself be one of the files you output" in mysql,
        mysql,
    )
    ok &= check(
        "instruction requires ONE shared config file across AWS and DB credentials, not separate files",
        "ONE INI file" in aws and "never split across separate config files" in aws,
        aws,
    )
    return ok


def eval_aws_instruction_requires_region_and_credentials():
    """Regression check for the 2026-08-13 20260813_003655 run and a follow-up gap found in
    the same instruction: ec2_manager.py's boto3.client('ec2') calls never passed region_name,
    and this machine has no ~/.aws/config or AWS_DEFAULT_REGION set -- botocore.exceptions.
    NoRegionError fired before the call even reached moto's mocking. AWS_TEST_INSTRUCTION
    already told the model to use region_name in the TEST file's own client creation, but
    AWS_INSTRUCTION (source code) said nothing about region -- or credentials -- at all.

    The credentials half: even once region_name was required, boto3.client('ec2',
    region_name=...) still never passed aws_access_key_id/aws_secret_access_key, so the
    'config file with credentials' the task asked for ended up only ever holding a region.
    Harmless under moto (which injects dummy credentials regardless), but the generated code
    would never authenticate against real AWS. Fixed the same way MYSQL_INSTRUCTION already
    requires 'user'/'password' by exact key name. Both region and credentials are the same
    underlying config-completeness requirement, so they're checked together here.

    The source builder no longer takes a needs_tests param (a needs_tests=False task's whole
    attempt is source-round-only), so there's only one case to check now."""
    ok = True
    source = build_source_system_instruction(external_system="AWS")

    ok &= check(
        "source AWS prompt requires region_name on every client",
        "region_name" in source and "NoRegionError" in source,
        source,
    )
    ok &= check(
        "region must be read from the config file, not hardcoded in the boto3 call",
        "region = us-east-1" in source and "config" in source.lower(),
        source,
    )
    ok &= check(
        "instruction requires exact credential key names in the config file",
        "aws_access_key_id" in source and "aws_secret_access_key" in source,
        source,
    )
    ok &= check(
        "instruction requires every boto3 call to pass all three explicitly",
        "aws_access_key_id=<config value>" in source and "aws_secret_access_key=<config value>" in source,
        source,
    )
    ok &= check(
        "instruction warns about NoCredentialsError, not just NoRegionError",
        "NoCredentialsError" in source,
        source,
    )
    return ok


def eval_aws_test_instruction_forbids_deprecated_moto_api():
    """Regression check for the 2026-08-12 20260812_235607 run: the model wrote
    @mock_aws('s3') and @mock_aws('ec2') across all 3 attempts -- neither the old,
    removed per-service moto API (mock_s3, mock_ec2) nor the current bare-decorator
    one. The original AWS_TEST_INSTRUCTION only said HOW to use mock_aws
    correctly; it never said what NOT to do, so the model wasn't warned off
    either wrong pattern."""
    ok = True
    test_instruction = build_test_system_instruction(external_system="AWS")
    ok &= check(
        "instruction explicitly forbids @mock_aws(...) with an argument",
        "mock_aws('s3')" in test_instruction or "no arguments" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction explicitly names the removed per-service decorators",
        "mock_s3" in test_instruction and "mock_ec2" in test_instruction,
        test_instruction,
    )
    return ok


def eval_aws_test_instruction_requires_self_contained_tests():
    """Regression check for the 2026-08-13 20260813_003655 run: test_get_all_s3
    failed with 'False is not true' because test_create_delete_s3 created then
    deleted 'test-bucket' before test_get_all_s3 ran (alphabetical unittest
    order), so the bucket test_get_all_s3 expected to find was already gone --
    it assumed state left behind by a different test instead of creating its
    own. AWS_TEST_INSTRUCTION said how to mock AWS but never said tests must be
    self-contained or that a test may only delete what it itself created."""
    ok = True
    test_instruction = build_test_system_instruction(external_system="AWS")
    ok &= check(
        "instruction requires each test to create its own resources",
        "self-contained" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction forbids deleting/terminating resources a test didn't create",
        "did not create" in test_instruction.lower() or "didn't create" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction requires a time-based unique resource name per test",
        "int(time.time())" in test_instruction,
        test_instruction,
    )
    ok &= check(
        "instruction forbids a fixed literal resource name reused across tests",
        "reused across multiple test methods" in test_instruction,
        test_instruction,
    )
    ok &= check(
        "instruction explicitly requires 'import time' when using time.time() for the name",
        "'import time'" in test_instruction,
        test_instruction,
    )
    return ok


def eval_needs_tests_gates_test_instructions():
    """After the two-round GENERATE split, needs_tests no longer gates prompt
    CONTENT -- it gates whether round 2 runs at all (see code_harness.py). The
    source builder never takes AWS_TEST_INSTRUCTION/MYSQL_TEST_INSTRUCTION (no
    param exists to include them); the test builder always includes them when
    the external system matches, since round 2 only ever runs when tests are
    needed in the first place."""
    ok = True
    ok &= check(
        "MySQL source instruction present",
        MYSQL_INSTRUCTION in build_source_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "MySQL test instruction never appears in the source builder's output",
        MYSQL_TEST_INSTRUCTION not in build_source_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "MySQL test instruction included in the test builder's output",
        MYSQL_TEST_INSTRUCTION in build_test_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "AWS source instruction present",
        AWS_INSTRUCTION in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS test instruction (moto) never appears in the source builder's output",
        AWS_TEST_INSTRUCTION not in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS test instruction (moto) included in the test builder's output",
        AWS_TEST_INSTRUCTION in build_test_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "source builder explicitly forbids writing a test file",
        "do not write any test file" in build_source_system_instruction().lower(),
    )
    ok &= check(
        "test builder explicitly says to write only the test file(s)",
        "write only the test file" in build_test_system_instruction().lower(),
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
        eval_source_instruction_forbids_unrequested_command_dispatcher(),
        eval_test_instruction_requires_test_file_to_run_its_tests(),
        eval_config_format_instruction_requires_ini_file_to_be_output(),
        eval_external_system_gates_aws_instruction(),
        eval_aws_instruction_requires_region_and_credentials(),
        eval_aws_test_instruction_forbids_deprecated_moto_api(),
        eval_aws_test_instruction_requires_self_contained_tests(),
        eval_needs_tests_gates_test_instructions(),
        eval_format_source_code_context(),
        eval_apply_external_system_override(),
        eval_apply_needs_tests_override(),
        eval_extract_external_system(),
        eval_extract_needs_tests(),
        eval_extract_test_steps_and_strip_test_content(),
    ]
    sys.exit(0 if all(results) else 1)
