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

import sys

from define import extract_external_system
from generate import AWS_INSTRUCTION, build_system_instruction, parse_generated_files

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
        eval_external_system_gates_aws_instruction(),
        eval_extract_external_system(),
    ]
    sys.exit(0 if all(results) else 1)
