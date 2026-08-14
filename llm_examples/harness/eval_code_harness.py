"""Eval for the two-round GENERATE retry state machine in code_harness.py.

Runs the REAL run_harness() end to end (real SAVE/STAGE/LINT/RESOLVE/COMPILE/
VALIDATE/EXECUTE against real files on disk under output/<run_id>/) with only
three things faked, via injectable parameters/monkeypatching:
  - DEFINE (code_harness.define_task) -- replaced with a fake returning a
    canned, already-confirmed spec, so no live Ollama call or input() prompt
    happens for it.
  - SAVE-permission confirmation (code_harness.confirm_save_permission) --
    replaced to always grant permission, so no input() prompt blocks the eval.
  - The two GENERATE calls (ask_local_model_for_source_code /
    ask_local_model_for_test_code) -- injected via run_harness()'s own
    parameters (the same pattern already used for `confirm`), returning
    canned FILE-block text and tracking call counts.

Regression motivation: before the two-round split, ANY failure anywhere in
an attempt regenerated everything from scratch next version, including
source code that had already passed every static check. These cases prove
the new state machine actually achieves the retry-efficiency win the split
was for: a test-only failure must not cause the source round to run again,
and a source failure must not let the test round run at all that version.

Run: python eval_code_harness.py
"""

import sys

import code_harness

VALID_SOURCE_RAW = "```python\ndef add(a, b):\n    return a + b\n```\n"

# References an undefined bare name -- valid syntax (passes LINT), but
# check_undefined_function_calls in RESOLVE catches it.
BROKEN_SOURCE_RAW = "```python\ndef add(a, b):\n    return helper_undefined(a, b)\n```\n"

VALID_TEST_RAW = (
    "```python\n"
    "import unittest\n"
    "from main import add\n\n"
    "class TestAdd(unittest.TestCase):\n"
    "    def test_add(self):\n"
    "        self.assertEqual(add(1, 2), 3)\n\n"
    'if __name__ == "__main__":\n'
    "    unittest.main()\n"
    "```\n"
)

# Same undefined-bare-name pattern as BROKEN_SOURCE_RAW, applied to the test
# round instead -- syntactically valid, RESOLVE-broken.
BROKEN_TEST_RAW = (
    "```python\n"
    "import unittest\n"
    "from main import add\n\n"
    "class TestAdd(unittest.TestCase):\n"
    "    def test_add(self):\n"
    "        result = helper_undefined(add(1, 2))\n"
    "        self.assertEqual(result, 3)\n\n"
    'if __name__ == "__main__":\n'
    "    unittest.main()\n"
    "```\n"
)

CANNED_SPEC = (
    "Input: two numbers a and b.\n\n"
    "Output: their sum.\n\n"
    "Steps:\n1. Add a and b.\n\n"
    "Test Steps:\n1. Verify add(1, 2) returns 3.\n\n"
    "External System called: None\n\n"
    "Tests needed: Yes"
)


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def _fake_define_task(confirm, logger, is_test=False):
    return CANNED_SPEC


def _fake_confirm_save_permission(run_dir, confirm):
    return True


def _fake_plan_task(spec, external_system, needs_tests, confirm, logger):
    """No PLAN-stage manifest -- same as a run where the user's task predates
    the PLAN stage. Keeps this eval's existing behavior (and its no-live-call
    guarantee) unchanged; plan-conformance-specific retry behavior gets its
    own dedicated eval case, not this one."""
    return []


def _patched(monkeypatches):
    """Apply {attr_name: value} to code_harness's module namespace, returning
    a restore function -- this codebase has no pytest/monkeypatch fixture, so
    this is the plain-script equivalent."""
    originals = {name: getattr(code_harness, name) for name in monkeypatches}
    for name, value in monkeypatches.items():
        setattr(code_harness, name, value)

    def restore():
        for name, value in originals.items():
            setattr(code_harness, name, value)

    return restore


def eval_test_only_failure_does_not_regenerate_source():
    """Case A: test round fails on attempt 1 (source succeeds), test round
    succeeds on attempt 2. The fake source generator must be called exactly
    once total across the whole run -- not once per attempt -- proving
    source_files stays cached across the test-only retry instead of being
    thrown away."""
    restore = _patched(
        {
            "define_task": _fake_define_task,
            "confirm_save_permission": _fake_confirm_save_permission,
            "plan_task": _fake_plan_task,
        }
    )
    try:
        source_calls = []
        test_calls = []

        def fake_source(source_spec, error_context="", external_system="", planned_files=None):
            source_calls.append(error_context)
            return VALID_SOURCE_RAW

        def fake_test(test_spec, source_files, error_context="", external_system="", planned_files=None):
            test_calls.append(error_context)
            return BROKEN_TEST_RAW if len(test_calls) == 1 else VALID_TEST_RAW

        result = code_harness.run_harness(
            confirm=lambda prompt: True,
            is_test=True,
            ask_local_model_for_source_code=fake_source,
            ask_local_model_for_test_code=fake_test,
        )

        ok = True
        ok &= check("run succeeds by attempt 2", result is True)
        ok &= check(
            "fake source generator called exactly once total, not once per attempt",
            len(source_calls) == 1,
            f"called {len(source_calls)} times",
        )
        ok &= check(
            "fake test generator called twice (broken v1, valid v2)",
            len(test_calls) == 2,
            f"called {len(test_calls)} times",
        )
        return ok
    finally:
        restore()


def eval_source_failure_skips_test_round_entirely():
    """Case B: source round fails on attempt 1, succeeds on attempt 2 --
    round 2 must never even run during attempt 1. Asserted indirectly (this
    harness exposes no per-attempt hook): the fake test generator always
    returns valid code immediately whenever it IS called, so if round 2 had
    incorrectly run during attempt 1's source failure, either the run would
    have succeeded a version early or the test generator's call count would
    exceed 1. Neither happens only if round 2 was correctly skipped for the
    whole of attempt 1."""
    restore = _patched(
        {
            "define_task": _fake_define_task,
            "confirm_save_permission": _fake_confirm_save_permission,
            "plan_task": _fake_plan_task,
        }
    )
    try:
        source_calls = []
        test_calls = []

        def fake_source(source_spec, error_context="", external_system="", planned_files=None):
            source_calls.append(error_context)
            return BROKEN_SOURCE_RAW if len(source_calls) == 1 else VALID_SOURCE_RAW

        def fake_test(test_spec, source_files, error_context="", external_system="", planned_files=None):
            test_calls.append(error_context)
            return VALID_TEST_RAW

        result = code_harness.run_harness(
            confirm=lambda prompt: True,
            is_test=True,
            ask_local_model_for_source_code=fake_source,
            ask_local_model_for_test_code=fake_test,
        )

        ok = True
        ok &= check("run succeeds by attempt 2", result is True)
        ok &= check(
            "fake source generator called twice (broken v1, valid v2)",
            len(source_calls) == 2,
            f"called {len(source_calls)} times",
        )
        ok &= check(
            "fake test generator called exactly once total -- never ran during attempt 1's source failure",
            len(test_calls) == 1,
            f"called {len(test_calls)} times",
        )
        return ok
    finally:
        restore()


# main.py, function 'add' -- attempt 1's fake source deliberately defines 'wrong_name' instead,
# a plan-conformance failure (not a lint/resolve/compile failure) that only check_plan_conformance
# catches; attempt 2 defines 'add' correctly.
PLANNED_MAIN_WITH_ADD = [
    {
        "filename": "main.py",
        "purpose": "add two numbers",
        "functions": ["add"],
        "entrypoint": True,
        "is_test": False,
    }
]

WRONG_FUNCTION_NAME_SOURCE_RAW = "```python\ndef wrong_name(a, b):\n    return a + b\n```\n"


def eval_plan_conformance_failure_retries_source_round_only():
    """Case C: the source round's own output is syntactically valid and passes
    lint/resolve/compile, but doesn't match the confirmed PLAN-stage manifest
    (attempt 1 defines 'wrong_name' instead of the planned 'add'). This must
    retry the source round alone, exactly like a lint/resolve/compile failure
    does -- the test round must never run during attempt 1."""

    def _fake_plan_task_with_plan(spec, external_system, needs_tests, confirm, logger):
        return PLANNED_MAIN_WITH_ADD

    restore = _patched(
        {
            "define_task": _fake_define_task,
            "confirm_save_permission": _fake_confirm_save_permission,
            "plan_task": _fake_plan_task_with_plan,
        }
    )
    try:
        source_calls = []
        test_calls = []

        def fake_source(source_spec, error_context="", external_system="", planned_files=None):
            source_calls.append(error_context)
            return WRONG_FUNCTION_NAME_SOURCE_RAW if len(source_calls) == 1 else VALID_SOURCE_RAW

        def fake_test(test_spec, source_files, error_context="", external_system="", planned_files=None):
            test_calls.append(error_context)
            return VALID_TEST_RAW

        result = code_harness.run_harness(
            confirm=lambda prompt: True,
            is_test=True,
            ask_local_model_for_source_code=fake_source,
            ask_local_model_for_test_code=fake_test,
        )

        ok = True
        ok &= check("run succeeds by attempt 2", result is True)
        ok &= check(
            "fake source generator called twice (plan-nonconforming v1, conforming v2)",
            len(source_calls) == 2,
            f"called {len(source_calls)} times",
        )
        ok &= check(
            "attempt 2's error_context names the missing planned function",
            len(source_calls) == 2 and "add" in source_calls[1],
            source_calls[1] if len(source_calls) == 2 else "n/a",
        )
        ok &= check(
            "fake test generator called exactly once total -- never ran during attempt 1's "
            "plan-conformance failure",
            len(test_calls) == 1,
            f"called {len(test_calls)} times",
        )
        return ok
    finally:
        restore()


def eval_run_harness_defaults_to_non_interactive_confirm():
    """run_harness()'s own default confirm= is auto_confirm, not default_confirm --
    non-interactive by default at the function level, not just via the __main__ CLI
    flag, so any other caller that doesn't override confirm= also gets it."""
    import inspect

    from confirm import auto_confirm

    default = inspect.signature(code_harness.run_harness).parameters["confirm"].default
    return check("run_harness's own confirm= default is auto_confirm", default is auto_confirm)


if __name__ == "__main__":
    results = [
        eval_test_only_failure_does_not_regenerate_source(),
        eval_source_failure_skips_test_round_entirely(),
        eval_plan_conformance_failure_retries_source_round_only(),
        eval_run_harness_defaults_to_non_interactive_confirm(),
    ]
    sys.exit(0 if all(results) else 1)
