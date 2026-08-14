"""Eval for systems/config_format.py's CONFIG_FORMAT_INSTRUCTION -- the shared,
system-agnostic config-file convention every system module composes into its own
SOURCE_INSTRUCTION.

Run (from the harness/ directory): python -m systems.eval_config_format
"""

import sys

from systems.config_format import CONFIG_FORMAT_INSTRUCTION


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_requires_ini_file_to_be_output():
    """Regression check for the 2026-08-13 20260813_013836 run (v3): ec2_manager.py
    and s3_manager.py both called config.read('db_config.ini'), but the model never
    once included a FILE block for db_config.ini itself across all 3 attempts.
    configparser.read() silently no-ops on a missing file, so this only surfaced as
    'KeyError: region' deep in EXECUTE. CONFIG_FORMAT_INSTRUCTION said to use an INI
    file but never said the model must actually output it as one of its files."""
    ok = True
    ok &= check(
        "requires the .ini file to be one of the output FILE blocks",
        "FILE: app_config.ini" in CONFIG_FORMAT_INSTRUCTION
        and "MUST itself be one of the files you output" in CONFIG_FORMAT_INSTRUCTION,
        CONFIG_FORMAT_INSTRUCTION,
    )
    ok &= check(
        "requires ONE shared config file across systems, not separate files",
        "ONE INI file" in CONFIG_FORMAT_INSTRUCTION
        and "never split across separate config files" in CONFIG_FORMAT_INSTRUCTION,
        CONFIG_FORMAT_INSTRUCTION,
    )
    return ok


def eval_requires_deterministic_placeholder_sentinel():
    """The '<<your_KEY_NAME>>' format lets validate.py detect a placeholder
    deterministically instead of guessing via loose marker words -- system-agnostic
    by living here rather than duplicated per system."""
    ok = True
    ok &= check(
        "requires the exact <<your_KEY_NAME>> placeholder form",
        "<<your_KEY_NAME>>" in CONFIG_FORMAT_INSTRUCTION,
        CONFIG_FORMAT_INSTRUCTION,
    )
    ok &= check(
        "gives a concrete copy-paste example, not just an abstract description",
        "<<your_aws_access_key_id>>" in CONFIG_FORMAT_INSTRUCTION
        or "<<your_password>>" in CONFIG_FORMAT_INSTRUCTION,
        CONFIG_FORMAT_INSTRUCTION,
    )
    ok &= check(
        "explicitly forbids other placeholder styles (fake-looking values, empty, etc.)",
        "no fake-looking value" in CONFIG_FORMAT_INSTRUCTION.lower()
        or "no empty value" in CONFIG_FORMAT_INSTRUCTION.lower(),
        CONFIG_FORMAT_INSTRUCTION,
    )
    return ok


if __name__ == "__main__":
    results = [
        eval_requires_ini_file_to_be_output(),
        eval_requires_deterministic_placeholder_sentinel(),
    ]
    sys.exit(0 if all(results) else 1)
