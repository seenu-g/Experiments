"""Orchestrator: wires DEFINE -> GENERATE -> LINT -> COMPILE -> VALIDATE -> EXECUTE.

Each version's attempt is saved unconditionally (pass or fail) under a flat,
versioned run folder (output/<run_id>/main_v1.py, ...) via SAVE, with
a *_v<N>.result file recording every stage's outcome, and a single run.log
capturing the full narrative of the run (see log.py) -- so a failed attempt
stays inspectable instead of being discarded.

One shared attempt budget (config.MAX_STAGE_ATTEMPTS): each version runs
generate -> save -> lint -> compile -> (validate + execute, only if compile
passed). Any failure feeds its error back into the next version's generate
call. VALIDATE checks the staged code's runtime prerequisites (importable
libraries, non-placeholder credentials) before EXECUTE runs it for real --
see validate.py for why lint/compile don't need this.

Requires Ollama running locally with config.LOCAL_MODEL pulled.
"""

import os
import time

from compile import compile_files
from confirm import default_confirm
from config import MAX_STAGE_ATTEMPTS
from define import define_task, extract_external_system
from execute import execute_in_sandbox
from generate import ask_local_model_for_code, parse_generated_files
from lint import lint_files
from log import get_logger
from save import (
    confirm_save_permission,
    make_run_dir,
    save_attempt,
    stage_for_execution,
    write_stage_result,
)
from validate import validate_environment


def _skip_downstream(run_dir, version, downstream_stages, skip_detail, log_reason, logger):
    """A stage failed -- record every stage after it in this version's pipeline as
    SKIPPED (never attempted, not itself a failure) and say so in the log."""
    for stage in downstream_stages:
        write_stage_result(run_dir, stage, version, None, skip_detail)
        logger.info(f"{stage.capitalize()} v{version}: SKIPPED ({log_reason})")


def run_harness(confirm=default_confirm, is_test: bool = False):
    run_id = time.strftime("%Y%m%d_%H%M%S")
    run_dir = make_run_dir(run_id)
    logger = get_logger(run_dir)
    logger.info(f"Run started: {run_id} (log: {os.path.join(run_dir, 'run.log')})")

    spec = define_task(confirm, logger, is_test=is_test)
    external_system = extract_external_system(spec)
    logger.info(f"External system: {external_system}")

    if not confirm_save_permission(run_dir, confirm):
        logger.info("Save permission denied by user. Aborting.")
        return False
    logger.info("Save permission granted; attempts will be written unconditionally from here.")

    error_context = ""
    for version in range(1, MAX_STAGE_ATTEMPTS + 1):
        logger.info(f"--- attempt v{version}/{MAX_STAGE_ATTEMPTS} ---")

        current_spec = spec if not error_context else f"{spec}\n\nFix this error:\n{error_context}"
        raw_output = ask_local_model_for_code(
            current_spec, error_context=error_context, external_system=external_system
        )
        files, entry_filename = parse_generated_files(raw_output, default_filename="main.py")

        versioned_paths, versioned_entry = save_attempt(files, entry_filename, run_dir, version)
        for path in versioned_paths:
            marker = " (ENTRYPOINT)" if path == versioned_entry else ""
            with open(path) as f:
                logger.info(f"Saved{marker} {path}:\n{f.read()}")

        py_paths = [p for p in versioned_paths if p.endswith(".py")]
        lint_passed, lint_detail = lint_files(py_paths)
        write_stage_result(run_dir, "lint", version, lint_passed, lint_detail)
        logger.info(f"Lint v{version}: {'PASS' if lint_passed else 'FAIL - ' + lint_detail}")
        if not lint_passed:
            _skip_downstream(
                run_dir, version, ["compile", "execute"], "skipped: lint failed", "lint failed", logger
            )
            error_context = lint_detail
            continue

        compile_passed, compile_detail = compile_files(py_paths)
        write_stage_result(run_dir, "compile", version, compile_passed, compile_detail)
        logger.info(f"Compile v{version}: {'PASS' if compile_passed else 'FAIL - ' + compile_detail}")
        if not compile_passed:
            _skip_downstream(
                run_dir, version, ["execute"], "skipped: compile failed", "compile failed", logger
            )
            error_context = compile_detail
            continue

        staged_dir, staged_entry = stage_for_execution(files, entry_filename, run_dir, version)
        staged_py_paths = [os.path.join(staged_dir, fname) for fname, _ in files if fname.endswith(".py")]
        staged_non_py_paths = [
            os.path.join(staged_dir, fname) for fname, _ in files if not fname.endswith(".py")
        ]

        validate_passed, validate_detail = validate_environment(
            staged_py_paths, staged_non_py_paths, logger
        )
        write_stage_result(run_dir, "validate", version, validate_passed, validate_detail)
        logger.info(
            f"Validate v{version}: {'PASS' if validate_passed else 'FAIL - ' + validate_detail}"
        )
        if not validate_passed:
            _skip_downstream(
                run_dir, version, ["execute"], f"skipped: {validate_detail}", "validate failed", logger
            )
            logger.info(
                f"Stopping run -- this is an environment problem regenerating code won't fix. "
                f"Address it and rerun the harness. See {run_dir}"
            )
            return False

        exit_code, stderr, stdout = execute_in_sandbox(staged_entry, cwd=staged_dir)
        execute_passed = exit_code == 0
        write_stage_result(
            run_dir, "execute", version, execute_passed, stderr if not execute_passed else ""
        )
        logger.info(
            f"Execute v{version}: {'PASS' if execute_passed else f'FAIL (exit {exit_code}) - ' + stderr}"
        )

        if execute_passed:
            logger.info(f"SUCCESS on v{version}: {run_dir}\nOutput:\n{stdout.strip()}")
            return True

        error_context = stderr

    logger.info(f"FAILED: no attempt succeeded within {MAX_STAGE_ATTEMPTS} versions. See {run_dir}")
    return False


if __name__ == "__main__":
    run_harness()
