"""EXECUTE stage: run the entrypoint in a subprocess and capture the result."""

import subprocess
import sys


def execute_in_sandbox(entry_filename: str, cwd: str) -> tuple:
    """Run the entrypoint via subprocess. Returns (exit_code, stderr, stdout)."""
    try:
        result = subprocess.run(
            [sys.executable, entry_filename],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        return result.returncode, result.stderr, result.stdout
    except subprocess.TimeoutExpired:
        return -1, "PROCESS_TIMEOUT: Script runtime exceeded maximum threshold.", ""
