"""EXECUTE stage: run the entrypoint in a subprocess and capture the result."""

import subprocess
import sys

from config import EXECUTE_TIMEOUT_SECONDS


def execute_in_sandbox(entry_filename: str, cwd: str, timeout: float = EXECUTE_TIMEOUT_SECONDS) -> tuple:
    """Run the entrypoint via subprocess. Returns (exit_code, stderr, stdout)."""
    try:
        result = subprocess.run(
            [sys.executable, entry_filename],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode, result.stderr, result.stdout
    except subprocess.TimeoutExpired:
        return -1, f"PROCESS_TIMEOUT: Script runtime exceeded maximum threshold ({timeout:.0f}s).", ""
