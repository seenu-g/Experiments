"""SAVE stage: persist every attempt (pass or fail) into a flat, versioned run
folder so failed attempts stay inspectable instead of being discarded.

Layout (one flat folder per run -- not one subfolder per version):
    output/<run_id>/
        main_v1.py
        lint_v1.result
        compile_v1.result
        execute_v1.result
        main_v2.py
        lint_v2.result
        ...
"""

import os

from config import OUTPUT_DIR

_PASS = "PASS"
_FAIL = "FAIL"
_SKIPPED = "SKIPPED"


def _versioned_name(filename: str, version: int) -> str:
    stem, ext = os.path.splitext(filename)
    return f"{stem}_v{version}{ext}"


def make_run_dir(run_id: str) -> str:
    run_dir = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def confirm_save_permission(run_dir: str, confirm) -> bool:
    """Asked once per run, before the first attempt is written."""
    return confirm(f"Save generated attempts to {run_dir}?")


def save_attempt(files: list, entry_filename: str, run_dir: str, version: int) -> tuple:
    """Writes each (filename, code) pair under its versioned name.

    Returns (versioned_paths, versioned_entry_path).
    """
    versioned_paths = []
    versioned_entry_path = None
    for filename, code in files:
        versioned_name = _versioned_name(filename, version)
        path = os.path.join(run_dir, versioned_name)
        with open(path, "w") as f:
            f.write(code)
        versioned_paths.append(path)
        if filename == entry_filename:
            versioned_entry_path = path
    return versioned_paths, versioned_entry_path or versioned_paths[-1]


def stage_for_execution(files: list, entry_filename: str, run_dir: str, version: int) -> tuple:
    """Writes original-named copies into run_dir/_exec_v<N>/ so 'import validator' style
    references between generated files resolve -- the flat, version-suffixed files saved
    by save_attempt() aren't importable by their original names, so execution needs its
    own untouched-name staging copy. Returns (staged_dir, staged_entry_filename)."""
    staged_dir = os.path.join(run_dir, f"_exec_v{version}")
    os.makedirs(staged_dir, exist_ok=True)
    for filename, code in files:
        with open(os.path.join(staged_dir, filename), "w") as f:
            f.write(code)
    return staged_dir, entry_filename


def write_stage_result(run_dir: str, stage: str, version: int, passed, detail: str = "") -> None:
    """passed: True/False/None (None means skipped -- prior stage already failed)."""
    if passed is None:
        status = _SKIPPED
    else:
        status = _PASS if passed else _FAIL
    path = os.path.join(run_dir, f"{stage}_v{version}.result")
    content = status if not detail else f"{status}\n{detail}"
    with open(path, "w") as f:
        f.write(content)
