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
from validate import (
    _looks_like_placeholder,
    _PLACEHOLDER_SENTINEL_RE,
    find_missing_libraries,
    find_placeholder_config_values,
    find_placeholder_credentials_in_py,
)


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


def eval_empty_and_mysql_tightening():
    with tempfile.TemporaryDirectory() as tmp:
        empty_path = os.path.join(tmp, "empty_field.ini")
        parser = configparser.ConfigParser()
        parser["database"] = {"host": "localhost", "user": "", "password": "Xk29!qLm7zR"}
        with open(empty_path, "w") as f:
            parser.write(f)

        fake_but_plausible_path = os.path.join(tmp, "fake_but_plausible.ini")
        parser2 = configparser.ConfigParser()
        parser2["database"] = {"host": "localhost", "user": "root", "password": "abc123"}
        with open(fake_but_plausible_path, "w") as f:
            parser2.write(f)

        ok = True

        empty_flagged = find_placeholder_config_values([empty_path])
        ok &= check(
            "empty value flagged even with no marker match and no external_system",
            ("database", "user", "") in empty_flagged.get(empty_path, []),
            empty_flagged,
        )

        not_mysql_flagged = find_placeholder_config_values([fake_but_plausible_path])
        ok &= check(
            "non-placeholder-looking password NOT flagged when external_system is unset",
            not_mysql_flagged == {},
            not_mysql_flagged,
        )

        mysql_flagged = find_placeholder_config_values([fake_but_plausible_path], external_system="MySQL Database")
        ok &= check(
            "same password IS flagged when external_system is MySQL (unconditional check)",
            ("database", "password", "abc123") in mysql_flagged.get(fake_but_plausible_path, [])
            and ("database", "user", "root") in mysql_flagged.get(fake_but_plausible_path, []),
            mysql_flagged,
        )
        ok &= check(
            "host isn't swept up by the MySQL user/password tightening",
            not any(key == "host" for _, key, _ in mysql_flagged.get(fake_but_plausible_path, [])),
            mysql_flagged,
        )
        return ok


def eval_aws_credential_tightening():
    """Same gap as MySQL's user/password, for AWS: ec2_manager.py's boto3.client() call
    never passed aws_access_key_id/aws_secret_access_key at all, and even if it had, a
    fake-but-plausible value like 'AKIAIOSFODNN7EXAMPLE' wouldn't match any placeholder
    marker. There's no point letting EXECUTE run against real AWS with a credential
    nobody actually supplied, so aws_access_key_id/aws_secret_access_key are now flagged
    unconditionally for AWS tasks, same as user/password are for MySQL."""
    with tempfile.TemporaryDirectory() as tmp:
        aws_ini_path = os.path.join(tmp, "app_config.ini")
        parser = configparser.ConfigParser()
        parser["DEFAULT"] = {
            "region": "us-east-1",
            # Plausible-looking but fake, deliberately avoiding any _PLACEHOLDER_MARKERS
            # word (e.g. AWS's own well-known "AKIAIOSFODNN7EXAMPLE" contains "EXAMPLE",
            # which would trigger the generic marker check regardless of this test's
            # AWS-specific unconditional check -- same "abc123" logic as the MySQL case.
            "aws_access_key_id": "AKIA1234567890ABCDEF",
            "aws_secret_access_key": "abcDEFghijKLMNOPqrstUVWXYZ0123456789ABCD",
        }
        with open(aws_ini_path, "w") as f:
            parser.write(f)

        ok = True

        not_aws_flagged = find_placeholder_config_values([aws_ini_path])
        ok &= check(
            "plausible-looking AWS credentials NOT flagged when external_system is unset",
            not_aws_flagged == {},
            not_aws_flagged,
        )

        aws_flagged = find_placeholder_config_values([aws_ini_path], external_system="AWS")
        flagged_keys = {key for _, key, _ in aws_flagged.get(aws_ini_path, [])}
        ok &= check(
            "same credentials ARE flagged when external_system is AWS (unconditional check)",
            {"aws_access_key_id", "aws_secret_access_key"} <= flagged_keys,
            flagged_keys,
        )
        ok &= check(
            "region isn't swept up by the AWS credential tightening",
            "region" not in flagged_keys,
            flagged_keys,
        )
        return ok


def eval_placeholder_sentinel_deterministic_format():
    """The '<<your_KEY_NAME>>' sentinel (see generate.CONFIG_FORMAT_INSTRUCTION) is a
    deterministic, system-agnostic placeholder format -- checked explicitly via
    _looks_like_placeholder rather than relying only on '<' already being in
    _PLACEHOLDER_MARKERS, so intent stays unambiguous even if that marker list changes."""
    ok = True
    ok &= check("exact sentinel form is recognized", _looks_like_placeholder("<<your_password>>"))
    ok &= check(
        "sentinel with surrounding whitespace is still recognized",
        _looks_like_placeholder("  <<your_aws_secret_access_key>>  "),
    )
    ok &= check(
        "sentinel is case-insensitive",
        _looks_like_placeholder("<<YOUR_API_KEY>>"),
    )
    ok &= check(
        "a real-looking value that ISN'T the sentinel and matches no marker word is still missed here",
        not _looks_like_placeholder("abc123"),
    )
    ok &= check(
        "a single-bracket near-miss doesn't false-negative -- '<' alone still trips the marker fallback",
        _looks_like_placeholder("<your_key>"),
    )
    return ok


def eval_placeholder_sentinel_no_false_positive_on_real_values():
    """The whole point of the sentinel over pure substring markers: a real value that
    innocently contains a marker WORD (not the sentinel shape) still gets flagged by the
    existing marker heuristic (documented, pre-existing behavior, unchanged) -- but this
    confirms the NEW sentinel regex itself doesn't introduce any additional false
    positives of its own on ordinary real-looking values."""
    ok = True
    ok &= check(
        "an ordinary AWS-style key is not matched by the sentinel regex itself",
        not bool(_PLACEHOLDER_SENTINEL_RE.match("AKIA1234567890ABCDEF")),
    )
    ok &= check(
        "a real URL is not matched by the sentinel regex itself",
        not bool(_PLACEHOLDER_SENTINEL_RE.match("https://example.org/api")),
    )
    return ok


def eval_find_placeholder_credentials_in_py():
    """Regression check for the 2026-08-12 20260812_212915 run: the model wrote
    credentials into config.py as a Python dict instead of a .ini file, and VALIDATE
    had no check for that -- it only ever scanned .ini files."""
    with tempfile.TemporaryDirectory() as tmp:
        config_py_path = os.path.join(tmp, "config.py")
        with open(config_py_path, "w") as f:
            f.write(
                "# MySQL configuration file\n"
                "config = {\n"
                "    'user': 'your_username',\n"
                "    'password': 'your_password'\n"
                "}\n"
            )

        manager_py_path = os.path.join(tmp, "db_manager.py")
        with open(manager_py_path, "w") as f:
            f.write(
                "def create_user(username, password, db_name):\n"
                "    conn = connect_to_db()\n"
                "    cursor = conn.cursor()\n"
                "    cursor.execute(f\"CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password}'\")\n"
            )

        real_config_py_path = os.path.join(tmp, "real_config.py")
        with open(real_config_py_path, "w") as f:
            f.write("config = {\n    'user': 'svc_app',\n    'password': 'Xk29!qLm7zR'\n}\n")

        ok = True

        found = find_placeholder_credentials_in_py([config_py_path])
        found_keys = {(key, value) for _, key, value, _, _ in found}
        ok &= check(
            "placeholder credentials in config.py detected",
            found_keys == {("user", "your_username"), ("password", "your_password")},
            found_keys,
        )

        manager_found = find_placeholder_credentials_in_py([manager_py_path])
        ok &= check(
            "function parameters/kwargs (unquoted values) are NOT falsely flagged",
            manager_found == [],
            manager_found,
        )

        real_found = find_placeholder_credentials_in_py([real_config_py_path])
        ok &= check(
            "real-looking quoted credentials NOT flagged when external_system is unset",
            real_found == [],
            real_found,
        )

        real_found_mysql = find_placeholder_credentials_in_py([real_config_py_path], external_system="MySQL")
        real_found_mysql_keys = {(key, value) for _, key, value, _, _ in real_found_mysql}
        ok &= check(
            "real-looking quoted credentials ARE flagged when external_system=MySQL (unconditional check)",
            real_found_mysql_keys == {("user", "svc_app"), ("password", "Xk29!qLm7zR")},
            real_found_mysql_keys,
        )

        # Verify the reported spans actually point at the value text, so a
        # splice-based rewrite (start:end replaced with the new value) is correct.
        path, key, old_value, start, end = found[0]
        with open(path) as f:
            content = f.read()
        ok &= check(
            "reported span slices out exactly the flagged value",
            content[start:end] == old_value,
            f"content[{start}:{end}] = {content[start:end]!r}, expected {old_value!r}",
        )

        return ok


def eval_find_placeholder_config_values_catches_sentinel_end_to_end():
    """Integration case: the sentinel is caught through the real find_placeholder_config_values
    path (not just the unit-level _looks_like_placeholder check above), for a key that ISN'T
    on any always_flag_keys list -- proving the sentinel alone, with no external_system context
    at all, is enough to flag it. System-agnostic by construction."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "azure_config.ini")
        parser = configparser.ConfigParser()
        parser["DEFAULT"] = {
            "region": "eastus",
            "subscription_id": "<<your_subscription_id>>",
        }
        with open(path, "w") as f:
            parser.write(f)

        flagged = find_placeholder_config_values([path])
        flagged_keys = {key for _, key, _ in flagged.get(path, [])}
        ok = True
        ok &= check(
            "sentinel value flagged with no external_system set at all (system-agnostic)",
            "subscription_id" in flagged_keys,
            flagged_keys,
        )
        ok &= check("real-looking region value NOT flagged", "region" not in flagged_keys, flagged_keys)
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
        eval_empty_and_mysql_tightening(),
        eval_aws_credential_tightening(),
        eval_find_placeholder_credentials_in_py(),
        eval_placeholder_sentinel_deterministic_format(),
        eval_placeholder_sentinel_no_false_positive_on_real_values(),
        eval_find_placeholder_config_values_catches_sentinel_end_to_end(),
        eval_input_with_timeout_raises_on_no_response(),
    ]
    sys.exit(0 if all(results) else 1)
