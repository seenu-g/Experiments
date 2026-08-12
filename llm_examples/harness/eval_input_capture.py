"""Eval for record_confirmed_prompt()'s de-duplication in input_capture.py.

Regression motivation: input/user_prompts.txt already has the same EC2/S3
description recorded 3 times verbatim (2026-08-12, 18:07/18:18/18:32) because
every confirmed run appended unconditionally, even when it was the exact same
prompt as a prior entry.

Run: python eval_input_capture.py
"""

import os
import sys
import tempfile

import input_capture


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_duplicate_prompt_not_appended():
    with tempfile.TemporaryDirectory() as tmp:
        input_capture.INPUT_DIR = tmp
        input_capture.USER_PROMPTS_FILE = os.path.join(tmp, "user_prompts.txt")
        input_capture.TEST_PROMPTS_FILE = os.path.join(tmp, "test_prompts.txt")

        description = "Write a function that adds two numbers."
        input_capture.record_confirmed_prompt(description)
        input_capture.record_confirmed_prompt(description)
        input_capture.record_confirmed_prompt(description)

        with open(input_capture.USER_PROMPTS_FILE) as f:
            lines = [line for line in f if line.strip()]

        ok = True
        ok &= check("exact duplicate recorded only once", len(lines) == 1, lines)
        ok &= check("the one line has the description", description in lines[0], lines)
        return ok


def eval_different_prompts_both_recorded():
    with tempfile.TemporaryDirectory() as tmp:
        input_capture.INPUT_DIR = tmp
        input_capture.USER_PROMPTS_FILE = os.path.join(tmp, "user_prompts.txt")
        input_capture.TEST_PROMPTS_FILE = os.path.join(tmp, "test_prompts.txt")

        input_capture.record_confirmed_prompt("Write a sorting function.")
        input_capture.record_confirmed_prompt("Write a searching function.")

        with open(input_capture.USER_PROMPTS_FILE) as f:
            lines = [line for line in f if line.strip()]

        return check("two distinct prompts both get recorded", len(lines) == 2, lines)


def eval_test_and_user_prompts_stay_separate():
    with tempfile.TemporaryDirectory() as tmp:
        input_capture.INPUT_DIR = tmp
        input_capture.USER_PROMPTS_FILE = os.path.join(tmp, "user_prompts.txt")
        input_capture.TEST_PROMPTS_FILE = os.path.join(tmp, "test_prompts.txt")

        description = "Same description used in both a real run and a test run."
        input_capture.record_confirmed_prompt(description, is_test=False)
        input_capture.record_confirmed_prompt(description, is_test=True)

        with open(input_capture.USER_PROMPTS_FILE) as f:
            user_lines = [line for line in f if line.strip()]
        with open(input_capture.TEST_PROMPTS_FILE) as f:
            test_lines = [line for line in f if line.strip()]

        ok = True
        ok &= check("user_prompts.txt got its entry", len(user_lines) == 1, user_lines)
        ok &= check(
            "test_prompts.txt got its own entry too (dedup is per-file, not global)",
            len(test_lines) == 1,
            test_lines,
        )
        return ok


if __name__ == "__main__":
    results = [
        eval_duplicate_prompt_not_appended(),
        eval_different_prompts_both_recorded(),
        eval_test_and_user_prompts_stay_separate(),
    ]
    sys.exit(0 if all(results) else 1)
