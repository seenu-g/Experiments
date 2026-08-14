"""PLAN stage: between DEFINE and GENERATE, confirm a concrete file manifest
(filenames, purpose, planned top-level functions/classes, which GENERATE round
each belongs to) grounded in the already-confirmed spec.

Mirrors define.py's restate -> extract -> confirm-loop shape exactly, including
reusing systems.config_format.CONFIG_FORMAT_INSTRUCTION verbatim when the task
touches a system that needs a config file, so config-file requirements are
expressed identically everywhere they apply.

Why: GENERATE (and every retry) otherwise invents file/function structure fresh,
silently, with no chance to catch a missing file (e.g. a referenced but never
generated db_config.ini) or an invented, unrequested file/function before code is
actually written. resolve.check_plan_conformance checks the real GENERATE output
against the manifest this stage produces.
"""

import re

import ollama

from config import LOCAL_MODEL, OLLAMA_KEEP_ALIVE
from systems import ALL_SYSTEMS
from systems.config_format import CONFIG_FORMAT_INSTRUCTION

# Tolerates both the plain 'FILE: <name>' form this stage instructs, and GENERATE's own
# '# === FILE: <name> ===' convention -- the model has been observed drifting into the
# latter starting from the SECOND file block onward (2026-08-15, the 20260815_031255 run:
# only app_config.ini used the plain form; every file after it used '# === FILE: X ===',
# which the old plain-only regex didn't match at all, silently merging ec2_manager.py,
# s3_manager.py, logger.py, and everything else into app_config.ini's own content --
# planned_files ended up with exactly one entry, so check_plan_conformance had nothing
# to check the genuinely-missing logger.py against). Same failure shape as the
# inline-'(ENTRYPOINT)' bug already fixed in generate.FILE_HEADER_RE -- a format
# deviation must never silently swallow every file block after the first.
FILE_BLOCK_HEADER_RE = re.compile(
    r"^(?:#\s*===\s*)?FILE:\s*(?P<fname>\S+?)(?:\s*===)?\s*$", re.MULTILINE
)


def _split_top_level_functions(functions_raw: str) -> list[str]:
    """Split a FUNCTIONS field on commas that separate distinct functions --
    NOT commas inside a single function's own parameter list. A naive
    functions_raw.split(",") on 'create_instance(instance_type, ami_id, ...),
    delete_instance(instance_id)' breaks each PARAMETER out as if it were its
    own separate function name (observed: the 2026-08-14 20260814_164832 run,
    where check_plan_conformance then falsely demanded top-level 'ami_id',
    'key_pair_name', etc. definitions -- names that were never planned
    functions at all, just parameters of one -- and the model, told to define
    them, added bogus top-level globals to satisfy the false requirement)."""
    parts = []
    depth = 0
    current = []
    for char in functions_raw:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def _bare_function_name(signature: str) -> str:
    """'create_x(name, region)' -> 'create_x' -- strips the signature so the
    name can be matched against a generated file's top-level defs."""
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", signature)
    return match.group(1) if match else signature.strip()


def build_plan_instruction(external_system: str = "", needs_tests: bool = False) -> str:
    if needs_tests:
        round_field_instruction = (
            "ROUND: <source/test> -- 'test' only for a file whose entire purpose is verifying "
            "behavior (a unit test file); every other file -- production code, config files, "
            "helper/tools modules -- is 'source'."
        )
        test_coverage_instruction = (
            "\n\nFor any file with ROUND: test, FUNCTIONS must NEVER be 'N/A' -- list exactly "
            "one test function per source function this test file exercises, named "
            "'test_<function_name>()' matching that SOURCE function's name exactly. E.g. if a "
            "source file plans 'create_x(name), delete_x(name)', its test file's FUNCTIONS must "
            "list 'test_create_x(), test_delete_x()' -- one test per source function, in the "
            "same order, never combining several operations into a single test and never "
            "omitting one. This is what actually gets checked and enforced after code is "
            "generated (see PLAN conformance) -- an 'N/A' or a merged test here means that "
            "check can't catch a source function nothing ever actually verifies."
        )
    else:
        round_field_instruction = (
            "Omit the ROUND field entirely for every file -- this task has no separate test "
            "round, every planned file is implicitly source."
        )
        test_coverage_instruction = ""

    instruction = (
        "The user's coding request has already been confirmed as the spec you're given below. "
        "Before any code is written, restate it as a concrete file manifest -- one block per "
        "file, in this EXACT format, describing structure only, never implementation:\n\n"
        "FILE: <filename>\n"
        "PURPOSE: <one line describing what this file is for>\n"
        "FUNCTIONS: <comma-separated top-level function/class names this file will define, e.g. "
        "'create_x(name), delete_x(name)' -- or 'N/A' for a file with no functions (e.g. a config "
        "file)>\n"
        "ENTRYPOINT: <yes/no -- yes for exactly one file across the whole plan, the one that will "
        "be run directly>\n"
        f"{round_field_instruction}\n\n"
        "List files in creation order: a file that imports another must come after the file it "
        "imports. Put the entrypoint file last. Describe files and function signatures only, not "
        "implementation -- do not write any code in this response."
        f"{test_coverage_instruction}"
    )

    if any(system.NEEDS_CONFIG_FILE and system.matches(external_system) for system in ALL_SYSTEMS):
        instruction += (
            "\n\n" + CONFIG_FORMAT_INSTRUCTION + " If any planned function will need credentials "
            "or a region, a `.ini` config file for them MUST be its own separate FILE block in "
            "this plan" + (", with ROUND: source." if needs_tests else ".")
        )

    return instruction


def restate_plan(spec: str, external_system: str = "", needs_tests: bool = False) -> str:
    """Ask the model to restate the confirmed spec as a file manifest."""
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": build_plan_instruction(external_system, needs_tests)},
            {"role": "user", "content": spec},
        ],
        options={"temperature": 0.1},
        keep_alive=OLLAMA_KEEP_ALIVE,
    )
    return response["message"]["content"].strip()


def extract_planned_files(plan_text: str) -> list[dict]:
    """Parse a restate_plan() reply into PlannedFile dicts: {filename, purpose,
    functions (bare names), entrypoint, is_test}. Returns [] if the reply has no
    parseable FILE: blocks at all."""
    headers = list(FILE_BLOCK_HEADER_RE.finditer(plan_text))

    planned_files = []
    for i, header in enumerate(headers):
        filename = header.group("fname")
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(plan_text)
        block = plan_text[start:end]

        purpose_match = re.search(r"PURPOSE:\s*(.+)", block)
        functions_match = re.search(r"FUNCTIONS:\s*(.+)", block)
        entrypoint_match = re.search(r"ENTRYPOINT:\s*(.+)", block)
        round_match = re.search(r"ROUND:\s*(.+)", block)

        functions_raw = functions_match.group(1).strip() if functions_match else "N/A"
        functions = (
            []
            if functions_raw.strip().upper() == "N/A"
            else [_bare_function_name(sig) for sig in _split_top_level_functions(functions_raw)]
        )

        planned_files.append(
            {
                "filename": filename,
                "purpose": purpose_match.group(1).strip() if purpose_match else "",
                "functions": functions,
                "entrypoint": bool(
                    entrypoint_match and entrypoint_match.group(1).strip().lower().startswith("y")
                ),
                "is_test": bool(
                    round_match and round_match.group(1).strip().lower().startswith("test")
                ),
            }
        )

    return planned_files


def plan_task(spec: str, external_system: str, needs_tests: bool, confirm, logger) -> list[dict]:
    """Loop: restate the spec as a file plan -> confirm, until the user accepts it.

    No attempt cap -- this is a human confirming intent, not an automated repair loop,
    same as define.define_task's confirm loop.
    """
    current_spec = spec
    while True:
        plan_text = restate_plan(current_spec, external_system, needs_tests)
        logger.info(f"Proposed file plan:\n{plan_text}")
        planned_files = extract_planned_files(plan_text)

        if confirm("Is this plan correct?"):
            logger.info("Plan confirmed by user.")
            return planned_files

        logger.info("Plan rejected by user; asking for feedback and regenerating.")
        feedback = input(
            "What should change about the file plan? (you can reference the plan above): "
        ).strip()
        current_spec = current_spec.rstrip() + f"\n\nUser feedback on the file plan: {feedback}"
