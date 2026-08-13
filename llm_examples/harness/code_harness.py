"""Orchestrator: wires DEFINE -> GENERATE (source) -> GENERATE (test) -> LINT ->
RESOLVE -> COMPILE -> VALIDATE -> EXECUTE.

Two ordered GENERATE calls per attempt, not one: source code first, then test
code grounded in the actual saved source content (see generate.py). This
mirrors how a person writes code-then-test and eliminates the "test
references something that was never actually written" bug class -- the
test-writing call is shown the real source file instead of guessing at it.

Each version's attempt is saved unconditionally (pass or fail) under a flat,
versioned run folder (output/<run_id>/main_v1.py, ...) via SAVE, with
a *_v<N>.result file recording every stage's outcome, and a single run.log
capturing the full narrative of the run (see log.py) -- so a failed attempt
stays inspectable instead of being discarded.

One shared attempt budget (config.MAX_STAGE_ATTEMPTS), but retry granularity
is now 3-tiered instead of "any failure regenerates everything":
- Source round's own LINT/RESOLVE/COMPILE fails -> only the source round
  regenerates next version (test round never even runs this version).
- Test round's own LINT/RESOLVE/COMPILE fails -> only the test round
  regenerates next version; the already-passing source files are reused
  as-is (source_files stays cached across versions).
- VALIDATE or EXECUTE fails (only reachable once both rounds' static checks
  already passed) -> ambiguous which side is wrong, so both rounds
  regenerate fresh next version.

RESOLVE catches a hallucinated cross-file/self reference (e.g. calling
module.SomeClass() when SomeClass is never defined anywhere) or a reference
to a config file that was never generated -- see resolve.py. VALIDATE checks
the staged code's runtime prerequisites (importable libraries, non-placeholder
credentials) before EXECUTE runs it for real -- see validate.py for why
lint/compile don't need this.

Requires Ollama running locally with config.LOCAL_MODEL pulled.
"""

import os
import time

from compile import compile_files
from confirm import default_confirm
from config import MAX_STAGE_ATTEMPTS
from define import (
    define_task,
    extract_external_system,
    extract_needs_tests,
    extract_test_steps,
    strip_test_content,
)
from execute import execute_in_sandbox
from generate import (
    ask_local_model_for_source_code,
    ask_local_model_for_test_code,
    parse_generated_files,
)
from lint import lint_files
from log import get_logger
from resolve import autofix_stdlib_module_imports, check_resolve_issues
from save import (
    confirm_save_permission,
    make_run_dir,
    save_attempt,
    stage_attempt,
    write_stage_result,
)
from validate import validate_environment


def _skip_downstream(run_dir, version, downstream_stages, skip_detail, log_reason, logger):
    """A stage failed -- record every stage after it in this version's pipeline as
    SKIPPED (never attempted, not itself a failure) and say so in the log."""
    for stage in downstream_stages:
        write_stage_result(run_dir, stage, version, None, skip_detail)
        logger.info(f"{stage.capitalize()} v{version}: SKIPPED ({log_reason})")


def run_harness(
    confirm=default_confirm,
    is_test: bool = False,
    ask_local_model_for_source_code=ask_local_model_for_source_code,
    ask_local_model_for_test_code=ask_local_model_for_test_code,
):
    run_id = time.strftime("%Y%m%d_%H%M%S")
    run_dir = make_run_dir(run_id)
    logger = get_logger(run_dir)
    logger.info(f"Run started: {run_id} (log: {os.path.join(run_dir, 'run.log')})")

    spec = define_task(confirm, logger, is_test=is_test)
    external_system = extract_external_system(spec)
    needs_tests = extract_needs_tests(spec)
    logger.info(f"External system: {external_system}")
    logger.info(f"Tests needed: {needs_tests}")

    # Split once, up front, so every version's source round sees zero test content and every
    # version's test round is grounded in the real source code instead of a spec paraphrase --
    # see define.strip_test_content's docstring for the bug this fixes.
    source_spec = strip_test_content(spec)
    logger.info(f"Source-round spec (test content stripped):\n{source_spec}")
    test_spec = extract_test_steps(spec) if needs_tests else ""
    if needs_tests:
        logger.info(f"Test-round spec (Test Steps only):\n{test_spec}")

    if not confirm_save_permission(run_dir, confirm):
        logger.info("Save permission denied by user. Aborting.")
        return False
    logger.info("Save permission granted; attempts will be written unconditionally from here.")

    source_files = None
    source_entry = None
    source_error_context = ""
    test_error_context = ""

    for version in range(1, MAX_STAGE_ATTEMPTS + 1):
        logger.info(f"--- attempt v{version}/{MAX_STAGE_ATTEMPTS} ---")

        if source_files is None:
            current_source_spec = (
                source_spec if not source_error_context
                else f"{source_spec}\n\nFix this error:\n{source_error_context}"
            )
            raw_output = ask_local_model_for_source_code(
                current_source_spec, error_context=source_error_context, external_system=external_system,
            )
            files, entry_filename = parse_generated_files(raw_output, default_filename="main.py")

            files, autofix_details = autofix_stdlib_module_imports(files)
            for detail in autofix_details:
                logger.info(f"Auto-fix (source) v{version}: {detail}")

            versioned_paths, versioned_entry = save_attempt(files, entry_filename, run_dir, version)
            for path in versioned_paths:
                marker = " (ENTRYPOINT)" if path == versioned_entry else ""
                with open(path) as f:
                    logger.info(f"Saved{marker} {path}:\n{f.read()}")

            # Staged here (not just before EXECUTE) so every check below sees the
            # same original, unversioned filenames the generated code's own import
            # statements actually reference -- RESOLVE in particular needs this:
            # `import test_database_manager` only matches a file literally named
            # test_database_manager.py, not the versioned test_database_manager_v3.py.
            staged_dir, staged_entry = stage_attempt(files, entry_filename, run_dir, version)
            staged_py_paths = [os.path.join(staged_dir, fname) for fname, _ in files if fname.endswith(".py")]
            staged_non_py_paths = [
                os.path.join(staged_dir, fname) for fname, _ in files if not fname.endswith(".py")
            ]

            downstream_after_lint = ["resolve", "compile"]
            downstream_after_resolve = ["compile"]
            downstream_after_compile = []
            if needs_tests:
                downstream_after_lint += ["test_lint", "test_resolve", "test_compile"]
                downstream_after_resolve += ["test_lint", "test_resolve", "test_compile"]
                downstream_after_compile += ["test_lint", "test_resolve", "test_compile"]
            downstream_after_lint.append("execute")
            downstream_after_resolve.append("execute")
            downstream_after_compile.append("execute")

            lint_passed, lint_detail = lint_files(staged_py_paths)
            write_stage_result(run_dir, "lint", version, lint_passed, lint_detail)
            logger.info(f"Lint v{version}: {'PASS' if lint_passed else 'FAIL - ' + lint_detail}")
            if not lint_passed:
                _skip_downstream(
                    run_dir, version, downstream_after_lint,
                    "skipped: source lint failed", "source lint failed", logger,
                )
                source_error_context = lint_detail
                continue

            staged_non_py_filenames = {os.path.basename(p) for p in staged_non_py_paths}
            resolve_passed, resolve_detail = check_resolve_issues(staged_py_paths, staged_non_py_filenames)
            write_stage_result(run_dir, "resolve", version, resolve_passed, resolve_detail)
            logger.info(f"Resolve v{version}: {'PASS' if resolve_passed else 'FAIL - ' + resolve_detail}")
            if not resolve_passed:
                _skip_downstream(
                    run_dir, version, downstream_after_resolve,
                    "skipped: source resolve failed", "source resolve failed", logger,
                )
                source_error_context = resolve_detail
                continue

            compile_passed, compile_detail = compile_files(staged_py_paths)
            write_stage_result(run_dir, "compile", version, compile_passed, compile_detail)
            logger.info(f"Compile v{version}: {'PASS' if compile_passed else 'FAIL - ' + compile_detail}")
            if not compile_passed:
                _skip_downstream(
                    run_dir, version, downstream_after_compile,
                    "skipped: source compile failed", "source compile failed", logger,
                )
                source_error_context = compile_detail
                continue

            source_files, source_entry = files, entry_filename

        # source_files is now populated -- either freshly generated above this
        # same version, or cached from an earlier version whose source round
        # already succeeded (a test-only retry skips straight to here).

        if needs_tests:
            current_test_spec = (
                test_spec if not test_error_context
                else f"{test_spec}\n\nFix this error:\n{test_error_context}"
            )
            raw_test_output = ask_local_model_for_test_code(
                current_test_spec, source_files, error_context=test_error_context, external_system=external_system,
            )
            test_files, test_entry_filename = parse_generated_files(
                raw_test_output, default_filename="test_main.py"
            )

            test_files, autofix_details = autofix_stdlib_module_imports(test_files)
            for detail in autofix_details:
                logger.info(f"Auto-fix (test) v{version}: {detail}")

            combined_files = source_files + test_files
            versioned_paths, versioned_entry = save_attempt(
                combined_files, test_entry_filename, run_dir, version
            )
            for path in versioned_paths:
                marker = " (ENTRYPOINT)" if path == versioned_entry else ""
                with open(path) as f:
                    logger.info(f"Saved{marker} {path}:\n{f.read()}")

            # Always stage the FULL combined file list (source + test), even on a
            # test-only retry where source_files didn't change this version -- so
            # stage_v<N>/ stays a complete, self-contained snapshot of exactly what
            # this version's checks ran against, without having to cross-reference
            # an earlier version's folder to find the source code it was tested with.
            staged_dir, staged_entry = stage_attempt(combined_files, test_entry_filename, run_dir, version)
            staged_py_paths = [
                os.path.join(staged_dir, fname) for fname, _ in combined_files if fname.endswith(".py")
            ]
            staged_non_py_paths = [
                os.path.join(staged_dir, fname) for fname, _ in combined_files if not fname.endswith(".py")
            ]

            test_lint_passed, test_lint_detail = lint_files(staged_py_paths)
            write_stage_result(run_dir, "test_lint", version, test_lint_passed, test_lint_detail)
            logger.info(f"Test_lint v{version}: {'PASS' if test_lint_passed else 'FAIL - ' + test_lint_detail}")
            if not test_lint_passed:
                _skip_downstream(
                    run_dir, version, ["test_resolve", "test_compile", "execute"],
                    "skipped: test lint failed", "test lint failed", logger,
                )
                test_error_context = test_lint_detail
                continue

            staged_non_py_filenames = {os.path.basename(p) for p in staged_non_py_paths}
            test_resolve_passed, test_resolve_detail = check_resolve_issues(
                staged_py_paths, staged_non_py_filenames
            )
            write_stage_result(run_dir, "test_resolve", version, test_resolve_passed, test_resolve_detail)
            logger.info(
                f"Test_resolve v{version}: {'PASS' if test_resolve_passed else 'FAIL - ' + test_resolve_detail}"
            )
            if not test_resolve_passed:
                _skip_downstream(
                    run_dir, version, ["test_compile", "execute"],
                    "skipped: test resolve failed", "test resolve failed", logger,
                )
                test_error_context = test_resolve_detail
                continue

            test_compile_passed, test_compile_detail = compile_files(staged_py_paths)
            write_stage_result(run_dir, "test_compile", version, test_compile_passed, test_compile_detail)
            logger.info(
                f"Test_compile v{version}: {'PASS' if test_compile_passed else 'FAIL - ' + test_compile_detail}"
            )
            if not test_compile_passed:
                _skip_downstream(
                    run_dir, version, ["execute"],
                    "skipped: test compile failed", "test compile failed", logger,
                )
                test_error_context = test_compile_detail
                continue

        # Shared final stage: VALIDATE + EXECUTE run once, on whichever staged set
        # is now current -- source-only (not needs_tests) or the combined
        # source+test set (needs_tests) staged above.
        validate_passed, validate_detail = validate_environment(
            staged_py_paths, staged_non_py_paths, logger, external_system=external_system
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

        # Ambiguous which side is actually wrong -- reset for a full retry.
        source_files = None
        source_entry = None
        source_error_context = stderr
        test_error_context = stderr

    logger.info(f"FAILED: no attempt succeeded within {MAX_STAGE_ATTEMPTS} versions. See {run_dir}")
    return False


if __name__ == "__main__":
    run_harness()
