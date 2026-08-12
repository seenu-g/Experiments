"""Blocking input()/confirm() with a timeout, for VALIDATE's environment prompts.

A plain input() blocks forever if nobody's at the keyboard. VALIDATE runs
unattended-ish (it's the stage that fires when a library or credential is
missing), so its prompts read on a background thread and give up after
`timeout` seconds instead of hanging the whole harness.
"""

import queue
import threading


class InputTimeout(Exception):
    """Raised when no response arrives within the timeout window."""


def input_with_timeout(prompt: str, timeout: float) -> str:
    result_queue = queue.Queue()

    def _read():
        try:
            result_queue.put(input(prompt))
        except EOFError:
            result_queue.put(None)

    # daemon=True: if we time out, this thread stays blocked on stdin forever,
    # but daemon status keeps it from preventing process exit.
    threading.Thread(target=_read, daemon=True).start()
    try:
        value = result_queue.get(timeout=timeout)
    except queue.Empty:
        raise InputTimeout(f"No response within {timeout:.0f}s")
    if value is None:
        raise InputTimeout("Input stream closed before a response was given")
    return value


def confirm_with_timeout(prompt: str, timeout: float) -> bool:
    answer = input_with_timeout(f"{prompt} [y/N]: ", timeout)
    return answer.strip().lower() == "y"
