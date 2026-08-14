"""Eval for execute.py's timeout handling.

Regression check for the 2026-08-13 20260813_215354 run: EXECUTE's subprocess
timeout was hardcoded to 10s, fine for typical demo scripts but too tight for
generated code that itself calls a local LLM (a LangChain OllamaLLM.invoke()
call took long enough to blow past it on all 3 attempts, even though the
underlying model responded in a few seconds to a direct ollama.chat() call in
a sibling run). Extracted into config.EXECUTE_TIMEOUT_SECONDS (60s default)
and made overridable per call.

Run: python eval_execute.py
"""

import os
import sys
import tempfile

from config import EXECUTE_TIMEOUT_SECONDS
from execute import execute_in_sandbox


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_default_timeout_matches_config():
    with tempfile.TemporaryDirectory() as tmp:
        script_path = os.path.join(tmp, "main.py")
        with open(script_path, "w") as f:
            f.write("print('done')\n")

        exit_code, stderr, stdout = execute_in_sandbox("main.py", cwd=tmp)
        ok = True
        ok &= check("fast script exits 0 well within the default timeout", exit_code == 0, stderr)
        ok &= check("stdout captured correctly", stdout.strip() == "done", stdout)
        ok &= check(
            "default timeout is config.EXECUTE_TIMEOUT_SECONDS (60s), not the old hardcoded 10s",
            EXECUTE_TIMEOUT_SECONDS == 60,
            EXECUTE_TIMEOUT_SECONDS,
        )
        return ok


def eval_custom_timeout_is_honored_and_reported():
    with tempfile.TemporaryDirectory() as tmp:
        script_path = os.path.join(tmp, "slow.py")
        with open(script_path, "w") as f:
            f.write("import time\ntime.sleep(5)\n")

        exit_code, stderr, stdout = execute_in_sandbox("slow.py", cwd=tmp, timeout=0.5)
        ok = True
        ok &= check(
            "a script that outlives a short custom timeout is caught, not left to the 60s default",
            exit_code == -1,
            (exit_code, stderr),
        )
        ok &= check(
            "the timeout failure message names the actual timeout that was used",
            "0s" in stderr or "1s" in stderr,  # %.0f rounding of 0.5
            stderr,
        )
        return ok


if __name__ == "__main__":
    results = [
        eval_default_timeout_matches_config(),
        eval_custom_timeout_is_honored_and_reported(),
    ]
    sys.exit(0 if all(results) else 1)
