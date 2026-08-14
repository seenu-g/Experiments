"""Eval for plan.py: extract_planned_files() parsing and build_plan_instruction()'s
config-file requirement for AWS/MySQL tasks.

Run: python eval_plan.py
"""

import sys

from plan import build_plan_instruction, extract_planned_files

MULTI_FILE_PLAN = """FILE: app_config.ini
PURPOSE: AWS region and credentials
FUNCTIONS: N/A
ENTRYPOINT: no
ROUND: source

FILE: ec2_manager.py
PURPOSE: create and delete EC2 instances
FUNCTIONS: create_instance(name), delete_instance(name)
ENTRYPOINT: yes
ROUND: source

FILE: test_ec2_manager.py
PURPOSE: unit tests for ec2_manager
FUNCTIONS: test_create_instance(), test_delete_instance()
ENTRYPOINT: no
ROUND: test
"""

SINGLE_FILE_NO_FUNCTIONS_PLAN = """FILE: app_config.ini
PURPOSE: database credentials
FUNCTIONS: N/A
ENTRYPOINT: no
"""

MISSING_ROUND_PLAN = """FILE: main.py
PURPOSE: reverse a string and print it
FUNCTIONS: reverse_string(text)
ENTRYPOINT: yes
"""

# Regression case for the 2026-08-14 20260814_164832 run: a naive split on every
# comma broke this single multi-parameter function's signature into 6 bogus
# "functions" (one per parameter), and check_plan_conformance then falsely
# demanded top-level 'ami_id'/'key_pair_name'/etc. definitions that were never
# planned functions at all.
MULTI_PARAM_FUNCTION_PLAN = """FILE: ec2_manager.py
PURPOSE: create and delete EC2 instances
FUNCTIONS: create_instance(instance_type, ami_id, key_pair_name, security_group_ids, subnet_id), delete_instance(instance_id)
ENTRYPOINT: yes
ROUND: source
"""


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_extract_planned_files_multi_file():
    files = extract_planned_files(MULTI_FILE_PLAN)
    ok = True
    ok &= check("parses all three files", len(files) == 3, f"got {len(files)}")

    by_name = {f["filename"]: f for f in files}
    ok &= check(
        "app_config.ini has no functions", by_name["app_config.ini"]["functions"] == []
    )
    ok &= check(
        "ec2_manager.py functions parsed as bare names",
        by_name["ec2_manager.py"]["functions"] == ["create_instance", "delete_instance"],
        str(by_name["ec2_manager.py"]["functions"]),
    )
    ok &= check(
        "ec2_manager.py marked as entrypoint", by_name["ec2_manager.py"]["entrypoint"] is True
    )
    ok &= check(
        "app_config.ini NOT marked as entrypoint",
        by_name["app_config.ini"]["entrypoint"] is False,
    )
    ok &= check(
        "test_ec2_manager.py is_test=True (ROUND: test)",
        by_name["test_ec2_manager.py"]["is_test"] is True,
    )
    ok &= check(
        "ec2_manager.py is_test=False (ROUND: source)",
        by_name["ec2_manager.py"]["is_test"] is False,
    )
    return ok


def eval_extract_planned_files_single_no_functions():
    files = extract_planned_files(SINGLE_FILE_NO_FUNCTIONS_PLAN)
    ok = True
    ok &= check("parses the single file", len(files) == 1, f"got {len(files)}")
    ok &= check("FUNCTIONS: N/A parses to empty list", files[0]["functions"] == [])
    ok &= check("purpose parsed correctly", files[0]["purpose"] == "database credentials")
    return ok


def eval_missing_round_defaults_to_source():
    files = extract_planned_files(MISSING_ROUND_PLAN)
    ok = True
    ok &= check("parses the file", len(files) == 1, f"got {len(files)}")
    ok &= check(
        "missing ROUND field defaults to is_test=False", files[0]["is_test"] is False
    )
    return ok


def eval_multi_param_function_signature_not_split_on_its_own_commas():
    files = extract_planned_files(MULTI_PARAM_FUNCTION_PLAN)
    ok = True
    ok &= check("parses the single file", len(files) == 1, f"got {len(files)}")
    ok &= check(
        "exactly the two real functions parsed, not one bogus entry per parameter",
        files[0]["functions"] == ["create_instance", "delete_instance"],
        str(files[0]["functions"]),
    )
    return ok


def eval_extract_planned_files_empty_reply_returns_empty_list():
    ok = check(
        "a reply with no FILE: blocks returns an empty list, not an error",
        extract_planned_files("I cannot help with that.") == [],
    )
    return ok


def eval_aws_instruction_requires_ini_file_block():
    instruction = build_plan_instruction(external_system="AWS", needs_tests=True)
    ok = True
    ok &= check(
        "AWS plan instruction requires a .ini FILE block for credentials",
        ".ini" in instruction and "FILE block" in instruction,
    )
    ok &= check(
        "AWS plan instruction tells the .ini file to be ROUND: source",
        "ROUND: source" in instruction,
    )
    ok &= check(
        "non-AWS/MySQL plan instruction has no config-file requirement",
        ".ini" not in build_plan_instruction(external_system="Ollama", needs_tests=False),
    )
    return ok


def eval_test_files_forbidden_from_na_functions():
    """Regression check for the 2026-08-15 20260815_003449 vs 20260814_203949 comparison:
    when PLAN's own FUNCTIONS field says 'N/A' for a test file, nothing constrains
    GENERATE's test structure at all -- one run merged create+delete into a single test
    and never wrote a dedicated get_all test; another run, whose PLAN explicitly
    enumerated one test function per source function, got consistent 1:1 coverage every
    time (check_plan_conformance enforced it). The inconsistency wasn't a GENERATE bug --
    it was PLAN itself being free to skip specifying structure. This must be closed at
    the instruction level: a test-round file's FUNCTIONS must never be N/A."""
    instruction = build_plan_instruction(needs_tests=True)
    ok = True
    ok &= check(
        "instruction forbids N/A functions for a test-round file",
        "FUNCTIONS must NEVER be 'N/A'" in instruction,
        instruction,
    )
    ok &= check(
        "instruction requires one test function per source function, named test_<name>()",
        "one test function per source function" in instruction and "test_<function_name>()" in instruction,
        instruction,
    )
    ok &= check(
        "instruction explicitly forbids merging several operations into a single test",
        "never combining several operations into a single test" in instruction,
        instruction,
    )
    ok &= check(
        "this rule is absent entirely when the task has no test round",
        "FUNCTIONS must NEVER be 'N/A'" not in build_plan_instruction(needs_tests=False),
    )
    return ok


def eval_needs_tests_gates_round_field_instruction():
    with_tests = build_plan_instruction(external_system="", needs_tests=True)
    without_tests = build_plan_instruction(external_system="", needs_tests=False)
    ok = True
    ok &= check(
        "needs_tests=True instructs the model to declare ROUND per file",
        "ROUND:" in with_tests and "'test' only for" in with_tests,
    )
    ok &= check(
        "needs_tests=False tells the model to omit ROUND entirely",
        "Omit the ROUND field entirely" in without_tests,
    )
    return ok


if __name__ == "__main__":
    results = [
        eval_extract_planned_files_multi_file(),
        eval_extract_planned_files_single_no_functions(),
        eval_missing_round_defaults_to_source(),
        eval_multi_param_function_signature_not_split_on_its_own_commas(),
        eval_extract_planned_files_empty_reply_returns_empty_list(),
        eval_aws_instruction_requires_ini_file_block(),
        eval_needs_tests_gates_round_field_instruction(),
        eval_test_files_forbidden_from_na_functions(),
    ]
    sys.exit(0 if all(results) else 1)
