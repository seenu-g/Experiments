"""Eval for the static checks in resolve.py.

Regression check #1, for the 2026-08-12 20260812_220825 run (v3): the
entrypoint was a self-import expecting a class that was never defined
anywhere --

    import test_database_manager
    test_database_manager.TestDatabaseManager().run()

-- which passed LINT and COMPILE (syntactically valid Python) and only failed
at EXECUTE with `AttributeError: partially initialized module
'test_database_manager' has no attribute 'TestDatabaseManager'`, burning a
whole GENERATE retry on something check_undefined_module_references() catches
for free.

Regression check #2, for the 2026-08-12 20260812_224411 run (v1): the model
followed MYSQL_TEST_INSTRUCTION's unique-timestamped-name guidance --
f'test_db_{int(time.time())}' -- but never added `import time`, so it passed
LINT/COMPILE and only failed at EXECUTE with `NameError: name 'time' is not
defined`. check_undefined_module_usage() catches this: a name used as
`X.attr` where X is never imported or defined anywhere in the file.

Regression check #3, for the 2026-08-12 20260812_225522 run: the SAME file
had both of the above problems at once (used `mysql.connector.Error` AND
`time.time()`, neither imported). The two checks used to each return on
their first match, so a single retry only ever learned about one problem;
the run burned all 3 attempts without the model ever hearing about both at
once. check_undefined_module_references() and check_undefined_module_usage()
now return every issue they find (a list), and check_resolve_issues()
combines all of them into one failure detail.

Regression check #4, for the 2026-08-13 20260813_001940 run (v2): a test
file called `create_s3_bucket('my-bucket')` -- a bare function call, not a
`module.attr` access -- without ever doing `from s3_manager import
create_s3_bucket`. check_undefined_module_usage() only checks `X.attr`
patterns, so it missed this; check_undefined_function_calls() adds the same
"never imported anywhere in this file" check for plain `foo(...)` calls.

Run: python eval_resolve.py
"""

import os
import sys
import tempfile

from resolve import (
    autofix_stdlib_module_imports,
    check_missing_config_file_references,
    check_resolve_issues,
    check_undefined_function_calls,
    check_undefined_module_references,
    check_undefined_module_usage,
)


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_self_import_undefined_class():
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "database_manager.py")
        with open(manager_path, "w") as f:
            f.write(
                "def create_database(db_name):\n    pass\n\n"
                "def delete_database(db_name):\n    pass\n"
            )

        entry_path = os.path.join(tmp, "test_database_manager.py")
        with open(entry_path, "w") as f:
            f.write("import test_database_manager\n\ntest_database_manager.TestDatabaseManager().run()\n")

        issues = check_undefined_module_references([manager_path, entry_path])
        ok = True
        ok &= check("self-import to an undefined class is caught", len(issues) == 1, issues)
        ok &= check(
            "detail names the missing class and its file",
            issues and "TestDatabaseManager" in issues[0] and "test_database_manager.py" in issues[0],
            issues,
        )
        return ok


def eval_valid_cross_file_reference_passes():
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "db_manager.py")
        with open(manager_path, "w") as f:
            f.write("def create_database(db_name):\n    pass\n\nclass DBManager:\n    pass\n")

        entry_path = os.path.join(tmp, "main.py")
        with open(entry_path, "w") as f:
            f.write("import db_manager\n\ndb_manager.create_database('test')\ndb_manager.DBManager()\n")

        issues = check_undefined_module_references([manager_path, entry_path])
        return check("valid function and class references pass", issues == [], issues)


def eval_typo_in_cross_file_call_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "db_manager.py")
        with open(manager_path, "w") as f:
            f.write("def create_database(db_name):\n    pass\n")

        entry_path = os.path.join(tmp, "main.py")
        with open(entry_path, "w") as f:
            f.write("import db_manager\n\ndb_manager.creat_database('test')\n")  # typo

        issues = check_undefined_module_references([manager_path, entry_path])
        ok = True
        ok &= check("typo'd cross-file function call is caught", len(issues) == 1, issues)
        ok &= check("detail names the typo'd function", issues and "creat_database" in issues[0], issues)
        return ok


def eval_stdlib_and_third_party_calls_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write(
                "import sqlite3\nimport mysql.connector\n\n"
                "conn = sqlite3.connect('x.db')\n"
                "conn2 = mysql.connector.connect(host='localhost')\n"
            )

        issues = check_undefined_module_references([path])
        return check("stdlib/third-party module calls are never flagged", issues == [], issues)


def eval_missing_import_usage_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_client.py")
        with open(path, "w") as f:
            f.write("db_name = f'test_db_{int(time.time())}'\nprint(db_name)\n")  # no `import time`

        issues = check_undefined_module_usage([path])
        ok = True
        ok &= check("time.time() without importing time is caught", len(issues) == 1, issues)
        ok &= check(
            "detail names the missing import",
            issues and "'time'" in issues[0] and "time.py" not in issues[0],
            issues,
        )
        return ok


def eval_actual_import_of_used_module_passes():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_client.py")
        with open(path, "w") as f:
            f.write("import time\n\ndb_name = f'test_db_{int(time.time())}'\nprint(db_name)\n")

        issues = check_undefined_module_usage([path])
        return check("time.time() WITH import time passes", issues == [], issues)


def eval_local_variables_and_params_not_falsely_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "db_manager.py")
        with open(path, "w") as f:
            f.write(
                "class DBManager:\n"
                "    def __init__(self, conn):\n"
                "        self.conn = conn\n\n"
                "    def run(self):\n"
                "        cursor = self.conn.cursor()\n"
                "        cursor.execute('SELECT 1')\n\n"
                "def use_it(arg):\n"
                "    return arg.upper()\n"
            )

        issues = check_undefined_module_usage([path])
        return check(
            "self/local vars/function params used as X.attr are not falsely flagged",
            issues == [],
            issues,
        )


def eval_bare_undefined_function_call_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "s3_manager.py")
        with open(manager_path, "w") as f:
            f.write(
                "def create_s3_bucket(bucket_name):\n    pass\n\n"
                "def delete_s3_bucket(bucket_name):\n    pass\n"
            )

        # Real bug: never imports create_s3_bucket/delete_s3_bucket from s3_manager.
        test_path = os.path.join(tmp, "s3_manager_test.py")
        with open(test_path, "w") as f:
            f.write(
                "from moto import mock_aws\n"
                "import unittest\n\n"
                "@mock_aws\n"
                "class TestS3Manager(unittest.TestCase):\n"
                "    def test_create_s3_bucket(self):\n"
                "        create_s3_bucket('my-bucket')\n\n"
                "    def test_delete_s3_bucket(self):\n"
                "        create_s3_bucket('my-bucket')\n"
                "        delete_s3_bucket('my-bucket')\n"
            )

        issues = check_undefined_function_calls([manager_path, test_path])
        ok = True
        ok &= check(
            "both undefined bare calls are caught",
            {"create_s3_bucket", "delete_s3_bucket"} == {
                issue.split("'")[1].split("(")[0] for issue in issues
            },
            issues,
        )
        ok &= check(
            "manager.py itself (defines, doesn't just call) is not flagged",
            all("s3_manager.py calls" not in issue for issue in issues),
            issues,
        )
        return ok


def eval_properly_imported_function_call_passes():
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "s3_manager.py")
        with open(manager_path, "w") as f:
            f.write("def create_s3_bucket(bucket_name):\n    pass\n")

        test_path = os.path.join(tmp, "s3_manager_test.py")
        with open(test_path, "w") as f:
            f.write(
                "from s3_manager import create_s3_bucket\n\n"
                "create_s3_bucket('my-bucket')\n"
            )

        issues = check_undefined_function_calls([manager_path, test_path])
        return check("properly imported function call is not flagged", issues == [], issues)


def eval_locally_defined_and_builtin_calls_not_falsely_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write(
                "def helper():\n    return 1\n\n"
                "class Thing:\n    pass\n\n"
                "def use_it(callback):\n"
                "    print(len('abc'))\n"      # builtin
                "    print(helper())\n"          # defined later in file, but scope-blind union still sees it
                "    print(Thing())\n"           # class instantiation
                "    callback()\n"               # function parameter used as a callable
            )

        issues = check_undefined_function_calls([path])
        return check(
            "locally defined functions/classes, builtins, and callback params are not falsely flagged",
            issues == [],
            issues,
        )


def eval_check_resolve_issues_combines_both():
    with tempfile.TemporaryDirectory() as tmp:
        clean_path = os.path.join(tmp, "clean.py")
        with open(clean_path, "w") as f:
            f.write("import time\n\nprint(time.time())\n")
        ok = True
        ok &= check(
            "combined check passes when both sub-checks pass",
            check_resolve_issues([clean_path]) == (True, ""),
        )

        missing_import_path = os.path.join(tmp, "missing_import.py")
        with open(missing_import_path, "w") as f:
            f.write("print(time.time())\n")
        passed, detail = check_resolve_issues([missing_import_path])
        ok &= check("combined check surfaces the missing-import failure too", passed is False, detail)
        return ok


def eval_multiple_simultaneous_issues_all_reported():
    """Regression check #3: both an undefined-module-reference issue and a
    missing-import issue in the SAME file must both show up in one failure,
    not just the first one found -- this is what let 20260812_225522 burn all
    3 retries without ever hearing about the 'time' bug until attempt 2."""
    with tempfile.TemporaryDirectory() as tmp:
        db_manager_path = os.path.join(tmp, "db_manager.py")
        with open(db_manager_path, "w") as f:
            f.write("def create_database(db_name):\n    pass\n")

        entry_path = os.path.join(tmp, "test_db_manager.py")
        with open(entry_path, "w") as f:
            f.write(
                "import db_manager\n\n"
                "test_db_name = f'test_db_{int(time.time())}'\n\n"  # 'time' never imported
                "def test_ops():\n"
                "    try:\n"
                "        db_manager.create_database(test_db_name)\n"
                "    except mysql.connector.Error as e:\n"  # 'mysql' never imported
                "        print(e)\n"
            )

        passed, detail = check_resolve_issues([db_manager_path, entry_path])
        ok = True
        ok &= check("both simultaneous issues fail the combined check", passed is False, detail)
        ok &= check("detail mentions the missing 'time' import", "'time'" in detail, detail)
        ok &= check("detail mentions the missing 'mysql' import", "'mysql'" in detail, detail)
        ok &= check(
            "detail reports both as separate lines, not just one",
            len(detail.splitlines()) == 2,
            detail,
        )
        return ok


def eval_autofix_adds_missing_stdlib_import():
    """Regression check for the 2026-08-13 20260813_013836 run: test_ec2_manager.py
    and test_s3_manager.py both used f'...{int(time.time())}' without 'import time',
    which used to fail RESOLVE and burn a whole regenerate-and-retry attempt on a
    fix that's completely unambiguous -- 'import time' is the only possible correct
    fix for a bare stdlib name. autofix_stdlib_module_imports() now patches this in
    place before RESOLVE even runs, so it never becomes a failure at all."""
    files = [
        ("s3_manager.py", "def create_bucket(name):\n    pass\n"),
        (
            "test_s3_manager.py",
            "from s3_manager import create_bucket\n\n"
            "def test_create():\n"
            "    name = f'bucket-{int(time.time())}'\n"
            "    create_bucket(name)\n",
        ),
    ]
    fixed_files, fixes = autofix_stdlib_module_imports(files)
    fixed = dict(fixed_files)
    ok = True
    ok &= check(
        "'import time' is prepended to the file that used it unqualified",
        fixed["test_s3_manager.py"].startswith("import time\n"),
        fixed["test_s3_manager.py"],
    )
    ok &= check(
        "the file that never used 'time' is untouched",
        fixed["s3_manager.py"] == files[0][1],
        fixed["s3_manager.py"],
    )
    ok &= check(
        "a human-readable fix description is returned",
        any("test_s3_manager.py" in f and "import time" in f for f in fixes),
        fixes,
    )

    passed, detail = check_resolve_issues(
        [_write_tmp("s3_manager.py", fixed["s3_manager.py"]), _write_tmp("test_s3_manager.py", fixed["test_s3_manager.py"])]
    )
    ok &= check("RESOLVE passes on the patched files", passed, detail)
    return ok


def eval_autofix_never_touches_non_stdlib_names():
    """A missing import of a name that ISN'T a real stdlib module (e.g. a typo'd
    or hallucinated cross-file function) must be left alone -- autofix only
    handles the unambiguous stdlib-module case; everything else still needs to
    go through the normal fail-and-retry RESOLVE path."""
    files = [("main.py", "def run():\n    return unknown_module.do_thing()\n")]
    fixed_files, fixes = autofix_stdlib_module_imports(files)
    ok = True
    ok &= check("non-stdlib undefined name is not auto-imported", fixed_files == files, fixed_files)
    ok &= check("no fix is reported for it", fixes == [], fixes)
    return ok


def eval_autofix_skips_non_python_and_unparseable_files():
    """A non-.py file (e.g. a config .ini) must pass through untouched, and a
    .py file with a syntax error must be left for LINT to report as-is rather
    than autofix silently swallowing it."""
    files = [
        ("config.ini", "[DEFAULT]\nregion = us-east-1\n"),
        ("broken.py", "def f(:\n    pass\n"),
    ]
    fixed_files, fixes = autofix_stdlib_module_imports(files)
    ok = True
    ok &= check("non-.py file passes through unchanged", fixed_files == files, fixed_files)
    ok &= check("no fixes reported for either file", fixes == [], fixes)
    return ok


def eval_missing_config_file_reference_is_caught():
    """Regression check for the 2026-08-13 20260813_013836 run (v3): ec2_manager.py
    and s3_manager.py both called config.read('db_config.ini') and then indexed
    config['DEFAULT']['region'], but the model never once generated db_config.ini
    across all 3 attempts. configparser.read() doesn't raise for a missing file,
    so LINT/RESOLVE's other checks/COMPILE/VALIDATE all passed, and it only
    surfaced as 'KeyError: region' deep in EXECUTE -- burning the run's entire
    attempt budget without the model ever being told the real problem."""
    with tempfile.TemporaryDirectory() as tmp:
        manager_path = os.path.join(tmp, "ec2_manager.py")
        with open(manager_path, "w") as f:
            f.write(
                "import configparser\n\n"
                "config = configparser.ConfigParser()\n"
                "config.read('db_config.ini')\n\n"
                "def get_region():\n"
                "    return config['DEFAULT']['region']\n"
            )

        ok = True
        issues = check_missing_config_file_references([manager_path], generated_non_py_filenames=set())
        ok &= check(
            "missing db_config.ini reference is caught when it was never generated",
            len(issues) == 1 and "db_config.ini" in issues[0],
            issues,
        )

        no_issues = check_missing_config_file_references(
            [manager_path], generated_non_py_filenames={"db_config.ini"}
        )
        ok &= check(
            "same reference passes when db_config.ini WAS generated this attempt",
            no_issues == [],
            no_issues,
        )

        passed, detail = check_resolve_issues([manager_path], generated_non_py_filenames=set())
        ok &= check("check_resolve_issues surfaces this failure too", passed is False, detail)

        passed_with_ini, _ = check_resolve_issues(
            [manager_path], generated_non_py_filenames={"db_config.ini"}
        )
        ok &= check("check_resolve_issues passes once the .ini is accounted for", passed_with_ini is True)

        passed_default, _ = check_resolve_issues([manager_path])
        ok &= check(
            "the config-file check is opt-in -- omitting generated_non_py_filenames skips it",
            passed_default is True,
        )

        return ok


def _write_tmp(filename, code):
    path = os.path.join(tempfile.mkdtemp(), filename)
    with open(path, "w") as f:
        f.write(code)
    return path


if __name__ == "__main__":
    results = [
        eval_self_import_undefined_class(),
        eval_valid_cross_file_reference_passes(),
        eval_typo_in_cross_file_call_is_caught(),
        eval_stdlib_and_third_party_calls_not_flagged(),
        eval_missing_import_usage_is_caught(),
        eval_actual_import_of_used_module_passes(),
        eval_local_variables_and_params_not_falsely_flagged(),
        eval_bare_undefined_function_call_is_caught(),
        eval_properly_imported_function_call_passes(),
        eval_locally_defined_and_builtin_calls_not_falsely_flagged(),
        eval_check_resolve_issues_combines_both(),
        eval_multiple_simultaneous_issues_all_reported(),
        eval_autofix_adds_missing_stdlib_import(),
        eval_autofix_never_touches_non_stdlib_names(),
        eval_autofix_skips_non_python_and_unparseable_files(),
        eval_missing_config_file_reference_is_caught(),
    ]
    sys.exit(0 if all(results) else 1)
