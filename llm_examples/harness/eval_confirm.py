"""Eval for confirm.py's auto_confirm() -- the default, non-interactive confirm()
used by code_harness.py's __main__ entrypoint.

Run: python eval_confirm.py
"""

import sys

from confirm import auto_confirm


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_auto_confirm_always_accepts():
    ok = True
    ok &= check("returns True for an arbitrary prompt", auto_confirm("Is this correct?") is True)
    ok &= check("returns True regardless of prompt content", auto_confirm("") is True)
    ok &= check(
        "returns True for a save-permission-style prompt",
        auto_confirm("Save generated attempts to output/run_id?") is True,
    )
    return ok


def eval_auto_confirm_never_blocks_on_stdin():
    """auto_confirm must never call input() -- it's the whole point of it. Verified
    by patching builtins.input to raise if called at all; the eval fails loudly
    instead of hanging if this regresses."""
    import builtins

    original_input = builtins.input

    def _blow_up_if_called(*args, **kwargs):
        raise AssertionError("auto_confirm must never call input()")

    builtins.input = _blow_up_if_called
    try:
        result = auto_confirm("Is this correct?")
        ok = check("completes without calling input()", result is True)
    except AssertionError as e:
        ok = check("completes without calling input()", False, str(e))
    finally:
        builtins.input = original_input

    return ok


if __name__ == "__main__":
    results = [
        eval_auto_confirm_always_accepts(),
        eval_auto_confirm_never_blocks_on_stdin(),
    ]
    sys.exit(0 if all(results) else 1)
