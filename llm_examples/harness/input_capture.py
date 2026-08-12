"""Captures every user-confirmed task description into input/.

Real user runs go to user_prompts.txt; the harness's own test/smoke runs
(is_test=True) go to test_prompts.txt instead, so the two never mix."""

import os
import time

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
USER_PROMPTS_FILE = os.path.join(INPUT_DIR, "user_prompts.txt")
TEST_PROMPTS_FILE = os.path.join(INPUT_DIR, "test_prompts.txt")


def record_confirmed_prompt(description: str, is_test: bool = False) -> None:
    os.makedirs(INPUT_DIR, exist_ok=True)
    target = TEST_PROMPTS_FILE if is_test else USER_PROMPTS_FILE
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {description}\n")
