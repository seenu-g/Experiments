"""
Unit tests for recover_heal_data.py's modular detect/fix/confirm schema-healing
pipeline. Run with: python test_recover_heal_data.py

Each test targets one function in isolation, plus a couple of scale/edge-case
scenarios (e.g. 100 columns instead of 4) run against the real local LLM
(phi3 via Ollama) to see actual behavior rather than assuming it.
"""
import io
import sys
import time
import unittest

import pandas as pd

from recover_heal_data import (
    EXPECTED_SCHEMA,
    confirm_healing,
    detect_mismatch,
    fix_mismatch,
    process_data,
)


class TestDetectMismatch(unittest.TestCase):
    def test_exact_match_no_mismatch(self):
        df = pd.DataFrame({c: ["x"] for c in EXPECTED_SCHEMA})
        self.assertFalse(detect_mismatch(df, EXPECTED_SCHEMA))

    def test_renamed_columns_is_mismatch(self):
        df = pd.DataFrame({
            "txn_id": ["A1"],
            "email_address": ["a@x.com"],
            "total_cost": [1.0],
            "date": ["2026-05-26"],
        })
        self.assertTrue(detect_mismatch(df, EXPECTED_SCHEMA))


class TestFixAndConfirmHealing(unittest.TestCase):
    def test_healable_mismatch_maps_correctly(self):
        df = pd.DataFrame({
            "txn_id": ["A1"],
            "email_address": ["a@x.com"],
            "total_cost": [1.0],
            "date": ["2026-05-26"],
        })
        healed = fix_mismatch(df, EXPECTED_SCHEMA)
        self.assertTrue(confirm_healing(healed, EXPECTED_SCHEMA))
        self.assertEqual(set(healed.columns), set(EXPECTED_SCHEMA))

    def test_extra_unmapped_column_is_dropped(self):
        df = pd.DataFrame({
            "txn_id": ["A1"],
            "email_address": ["a@x.com"],
            "total_cost": [1.0],
            "date": ["2026-05-26"],
            "internal_notes": ["vip"],
        })
        healed = fix_mismatch(df, EXPECTED_SCHEMA)
        self.assertNotIn("internal_notes", healed.columns)
        self.assertTrue(confirm_healing(healed, EXPECTED_SCHEMA))

    def test_missing_column_fails_confirmation(self):
        df = pd.DataFrame({
            "txn_id": ["A1"],
            "email_address": ["a@x.com"],
            "total_cost": [1.0],
        })
        healed = fix_mismatch(df, EXPECTED_SCHEMA)
        self.assertFalse(confirm_healing(healed, EXPECTED_SCHEMA))

    def test_process_data_raises_on_unrecoverable_drift(self):
        df = pd.DataFrame({
            "txn_id": ["A1"],
            "email_address": ["a@x.com"],
            "total_cost": [1.0],
        })
        with self.assertRaises(KeyError):
            process_data(df, EXPECTED_SCHEMA)


class TestScale(unittest.TestCase):
    """How the pipeline behaves as column count grows from 4 to 100."""

    def test_100_meaningless_columns_times_out(self):
        # Column names carry no semantic signal (src_col_i / field_i_expected),
        # so the LLM has nothing to match on. Combined with a 60s request
        # timeout (recover_heal_data.py's heal_schema), this is expected to
        # fail safely rather than hang forever.
        expected_100 = [f"field_{i}_expected" for i in range(100)]
        df = pd.DataFrame({f"src_col_{i}": [f"val{i}"] for i in range(100)})

        self.assertTrue(detect_mismatch(df, expected_100))

        t0 = time.time()
        with self.assertRaises(RuntimeError):
            fix_mismatch(df, expected_100)
        elapsed = time.time() - t0
        print(f"\n  [100 meaningless columns] failed after {elapsed:.1f}s (timeout=60s)")

    def test_100_semantically_named_columns(self):
        # Same column count, but names carry real semantic meaning this time
        # (e.g. cust_0_full_name -> customer_0_name), giving the LLM something
        # to actually match on. No timeout assumption here - just observe
        # what happens (pass/fail, elapsed time, mapping accuracy).
        expected_100 = [f"customer_{i}_name" for i in range(100)]
        df = pd.DataFrame({f"cust_{i}_full_name": [f"Person {i}"] for i in range(100)})

        t0 = time.time()
        try:
            healed = fix_mismatch(df, expected_100)
            elapsed = time.time() - t0
            ok = confirm_healing(healed, expected_100)
            print(f"\n  [100 semantic columns] healed={ok} in {elapsed:.1f}s, "
                  f"result columns={len(healed.columns)}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"\n  [100 semantic columns] {type(e).__name__}: {e} after {elapsed:.1f}s")


def run_with_clean_output(*test_case_classes):
    """Run each test individually, printing '<test_name>: STATUS' on its own
    line followed by that test's captured print/log output, then a blank
    line before the next test - instead of unittest's default interleaved
    dots-and-logs formatting.
    """
    total = 0
    failed = 0

    for test_class in test_case_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        for test in suite:
            total += 1
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            result = unittest.TestResult()
            test.run(result)
            sys.stdout = old_stdout

            if result.wasSuccessful():
                status = "PASS"
            elif result.errors:
                status = "ERROR"
                failed += 1
            else:
                status = "FAIL"
                failed += 1

            print(f"{test._testMethodName}: {status}")
            captured = buf.getvalue().strip()
            if captured:
                print(captured)
            for _, trace in result.failures + result.errors:
                print(trace)
            print()

    print(f"Ran {total} tests, {total - failed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_with_clean_output(
        TestDetectMismatch,
        TestFixAndConfirmHealing,
        TestScale,
    )
    sys.exit(0 if ok else 1)
