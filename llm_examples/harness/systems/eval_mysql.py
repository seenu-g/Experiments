"""Eval for systems/mysql.py's prompt instructions.

Run (from the harness/ directory): python -m systems.eval_mysql
"""

import sys

from generate import build_source_system_instruction, build_test_system_instruction
from systems.mysql import SOURCE_INSTRUCTION as MYSQL_INSTRUCTION, TEST_INSTRUCTION as MYSQL_TEST_INSTRUCTION


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_mysql_instruction_gated_by_external_system():
    """MySQL's SOURCE_INSTRUCTION must appear only when external_system actually
    mentions MySQL -- verified through generate.py's real dispatch, the
    integration point systems.mysql plugs into."""
    ok = True
    ok &= check(
        "MySQL block included when external_system=MySQL Database",
        MYSQL_INSTRUCTION in build_source_system_instruction(external_system="MySQL Database"),
    )
    ok &= check(
        "MySQL block excluded when external_system=AWS",
        MYSQL_INSTRUCTION not in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "MySQL block excluded when external_system=None",
        MYSQL_INSTRUCTION not in build_source_system_instruction(external_system="None"),
    )
    return ok


def eval_needs_tests_gates_mysql_test_instruction():
    """After the two-round GENERATE split, needs_tests no longer gates prompt
    CONTENT -- it gates whether round 2 runs at all (see code_harness.py). The
    source builder never includes MySQL's TEST_INSTRUCTION; the test builder
    always includes it when the external system matches, since round 2 only
    ever runs when tests are needed in the first place."""
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
    return ok


if __name__ == "__main__":
    results = [
        eval_mysql_instruction_gated_by_external_system(),
        eval_needs_tests_gates_mysql_test_instruction(),
    ]
    sys.exit(0 if all(results) else 1)
