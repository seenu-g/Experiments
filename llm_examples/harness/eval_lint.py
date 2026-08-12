"""Eval for lint_files() in lint.py.

Regression check for the 2026-08-12 20260812_233842 run: the model's
ENTRYPOINT file (main.py) and one test file (test_ec2_manager.py) came back
completely empty. An empty file is syntactically valid, so it trivially
passed LINT, COMPILE, RESOLVE, and EXECUTE (`python empty_file.py` just
exits 0) -- the harness reported "SUCCESS on v1" even though no EC2 code and
no EC2 tests were ever actually written or run.

Run: python eval_lint.py
"""

import os
import sys
import tempfile

from lint import lint_files


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_empty_file_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write("")
        passed, detail = lint_files([path])
        return check("completely empty file fails lint", passed is False, detail)


def eval_whitespace_only_file_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write("   \n\n\t\n")
        passed, detail = lint_files([path])
        return check("whitespace-only file fails lint", passed is False, detail)


def eval_comments_only_file_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write("# just a comment\n# another comment\n")
        passed, detail = lint_files([path])
        return check("comments-only file fails lint (comments produce no AST nodes)", passed is False, detail)


def eval_real_code_passes():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        passed, detail = lint_files([path])
        return check("file with real code still passes", passed is True, detail)


def eval_syntax_error_still_caught():
    """Regression guard: the new empty-file check must not weaken the existing
    ast.parse() syntax check."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write("def broken(:\n    pass\n")
        passed, detail = lint_files([path])
        ok = True
        ok &= check("syntax error is still caught", passed is False, detail)
        ok &= check("detail is the syntax error, not the empty-file message", "ast.parse" in detail, detail)
        return ok


if __name__ == "__main__":
    results = [
        eval_empty_file_fails(),
        eval_whitespace_only_file_fails(),
        eval_comments_only_file_fails(),
        eval_real_code_passes(),
        eval_syntax_error_still_caught(),
    ]
    sys.exit(0 if all(results) else 1)
