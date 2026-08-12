"""Eval for the pure detection helpers in validate.py.

validate_environment() itself is interactive (confirm()/input()), so this
covers the two building blocks it relies on: which imports are missing from
the environment, and which config values look like placeholders the model
invented rather than real credentials.

Run: python eval_validate.py
"""

import configparser
import os
import sys
import tempfile
import time

from timeout_input import InputTimeout, input_with_timeout
from validate import find_missing_libraries, find_placeholder_config_values


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_find_missing_libraries():
    with tempfile.TemporaryDirectory() as tmp:
        real_path = os.path.join(tmp, "uses_real_stdlib.py")
        with open(real_path, "w") as f:
            f.write("import os\nimport sys\nfrom collections import OrderedDict\n")

        fake_path = os.path.join(tmp, "uses_fake_lib.py")
        with open(fake_path, "w") as f:
            f.write("import definitely_not_a_real_package_xyz\n")

        local_import_path = os.path.join(tmp, "uses_sibling.py")
        with open(local_import_path, "w") as f:
            f.write("import uses_real_stdlib\n")  # a sibling generated file, not a library

        ok = True
        ok &= check(
            "stdlib-only file has no missing libraries",
            find_missing_libraries([real_path]) == [],
        )
        ok &= check(
            "fake package is detected as missing",
            find_missing_libraries([fake_path]) == ["definitely_not_a_real_package_xyz"],
        )
        ok &= check(
            "sibling generated-file import isn't flagged as a missing library",
            find_missing_libraries([local_import_path, real_path]) == [],
        )
        return ok


def eval_find_placeholder_config_values():
    with tempfile.TemporaryDirectory() as tmp:
        placeholder_path = os.path.join(tmp, "db_config.ini")
        parser = configparser.ConfigParser()
        parser["database"] = {"host": "localhost", "user": "root", "password": "password"}
        with open(placeholder_path, "w") as f:
            parser.write(f)

        real_path = os.path.join(tmp, "real_config.ini")
        parser2 = configparser.ConfigParser()
        parser2["database"] = {"host": "db-prod-01.internal.net", "user": "svc_app", "password": "Xk29!qLm7zR"}
        with open(real_path, "w") as f:
            parser2.write(f)

        not_ini_path = os.path.join(tmp, "notes.txt")
        with open(not_ini_path, "w") as f:
            f.write("password=password\n")

        ok = True
        flagged = find_placeholder_config_values([placeholder_path])
        ok &= check(
            "placeholder password flagged",
            flagged.get(placeholder_path) is not None
            and ("database", "password", "password") in flagged[placeholder_path],
            flagged,
        )

        real_flagged = find_placeholder_config_values([real_path])
        ok &= check("real-looking credentials not flagged", real_flagged == {}, real_flagged)

        ok &= check(
            "non-.ini files are ignored",
            find_placeholder_config_values([not_ini_path]) == {},
        )
        return ok


def eval_input_with_timeout_raises_on_no_response():
    """No real stdin is attached to this eval run, so input() hits EOF (or, on a
    real terminal with nobody typing, the timeout itself) either way proving the
    call doesn't hang the process forever."""
    start = time.time()
    raised = False
    try:
        input_with_timeout("unused prompt: ", timeout=0.5)
    except InputTimeout:
        raised = True
    elapsed = time.time() - start

    ok = True
    ok &= check("raises InputTimeout instead of hanging when nobody responds", raised)
    ok &= check("returns promptly rather than blocking indefinitely", elapsed < 3.0, f"took {elapsed:.2f}s")
    return ok


if __name__ == "__main__":
    results = [
        eval_find_missing_libraries(),
        eval_find_placeholder_config_values(),
        eval_input_with_timeout_raises_on_no_response(),
    ]
    sys.exit(0 if all(results) else 1)
