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

from define import _apply_external_system_override, extract_external_system, extract_needs_tests
from generate import (
    AWS_INSTRUCTION,
    AWS_TEST_INSTRUCTION,
    MYSQL_INSTRUCTION,
    MYSQL_TEST_INSTRUCTION,
    build_system_instruction,
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


def eval_external_system_gates_aws_instruction():
    ok = True
    ok &= check(
        "AWS block included when external_system=AWS",
        AWS_INSTRUCTION in build_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS block excluded when external_system=MySQL",
        AWS_INSTRUCTION not in build_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "AWS block excluded when external_system=None",
        AWS_INSTRUCTION not in build_system_instruction(external_system="None"),
    )
    ok &= check(
        "AWS block excluded when external_system=''",
        AWS_INSTRUCTION not in build_system_instruction(external_system=""),
    )
    ok &= check(
        "MySQL block included when external_system=MySQL Database",
        MYSQL_INSTRUCTION in build_system_instruction(external_system="MySQL Database"),
    )
    ok &= check(
        "MySQL block excluded when external_system=AWS",
        MYSQL_INSTRUCTION not in build_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS block excluded when external_system=MySQL Database",
        AWS_INSTRUCTION not in build_system_instruction(external_system="MySQL Database"),
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
    aws_with_tests = build_system_instruction(external_system="AWS", needs_tests=True)
    ok &= check(
        "instruction explicitly forbids @mock_aws(...) with an argument",
        "mock_aws('s3')" in aws_with_tests or "no arguments" in aws_with_tests.lower(),
        aws_with_tests,
    )
    ok &= check(
        "instruction explicitly names the removed per-service decorators",
        "mock_s3" in aws_with_tests and "mock_ec2" in aws_with_tests,
        aws_with_tests,
    )
    return ok


def eval_needs_tests_gates_test_instructions():
    ok = True
    ok &= check(
        "MySQL prod instruction present even when needs_tests=False",
        MYSQL_INSTRUCTION in build_system_instruction(external_system="MySQL", needs_tests=False),
    )
    ok &= check(
        "MySQL test instruction excluded when needs_tests=False",
        MYSQL_TEST_INSTRUCTION not in build_system_instruction(external_system="MySQL", needs_tests=False),
    )
    ok &= check(
        "MySQL test instruction included when needs_tests=True",
        MYSQL_TEST_INSTRUCTION in build_system_instruction(external_system="MySQL", needs_tests=True),
    )
    ok &= check(
        "AWS prod instruction present even when needs_tests=False",
        AWS_INSTRUCTION in build_system_instruction(external_system="AWS", needs_tests=False),
    )
    ok &= check(
        "AWS test instruction (moto) excluded when needs_tests=False",
        AWS_TEST_INSTRUCTION not in build_system_instruction(external_system="AWS", needs_tests=False),
    )
    ok &= check(
        "AWS test instruction (moto) included when needs_tests=True",
        AWS_TEST_INSTRUCTION in build_system_instruction(external_system="AWS", needs_tests=True),
    )
    ok &= check(
        "explicit 'do not write a test file' instruction present when needs_tests=False",
        "Do not write a test file" in build_system_instruction(needs_tests=False),
    )
    ok &= check(
        "explicit 'include a test file' instruction present when needs_tests=True",
        "Include a test file" in build_system_instruction(needs_tests=True),
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
        eval_external_system_gates_aws_instruction(),
        eval_aws_test_instruction_forbids_deprecated_moto_api(),
        eval_needs_tests_gates_test_instructions(),
        eval_apply_external_system_override(),
        eval_extract_external_system(),
        eval_extract_needs_tests(),
    ]
    sys.exit(0 if all(results) else 1)
