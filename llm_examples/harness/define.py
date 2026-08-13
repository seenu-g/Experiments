"""DEFINE stage: confirm the user's intent before any code is generated."""

import re

import ollama

from config import LOCAL_MODEL
from input_capture import record_confirmed_prompt


def restate_task(raw_description: str) -> str:
    """Ask the model to restate the user's task as a clear, structured spec."""
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Restate the user's coding request as a spec using exactly these six "
                    "labeled sections, plain text, no code, no preamble:\n\n"
                    "Input: <what data/values come in>\n"
                    "Output: <what is produced/returned>\n"
                    "Steps: <ordered list of the algorithm-level logic for the production code "
                    "only -- do NOT include writing tests, test scripts, or test clients here; "
                    "any such step belongs in Test Steps below instead. IMPORTANT: any requirement "
                    "about how the code must BEHAVE belongs here, even if the user phrased it in "
                    "testing language -- e.g. 'handle invalid input and raise an error', 'reject "
                    "negative numbers', 'validate the input' are behavior the implementation itself "
                    "must have, not test-writing, and belong in Steps even though the word 'test' "
                    "might appear near them in the request. Only put a step in Test Steps if it "
                    "describes writing verification code that checks/asserts behavior already "
                    "captured in Steps -- never a step that would introduce new behavior the "
                    "implementation doesn't otherwise have.>\n"
                    "Test Steps: <ordered list of steps specifically for writing/running "
                    "automated tests that verify the behavior above -- 'None' if the user didn't "
                    "ask for tests, verification, or a test client/script>\n"
                    "External System called: <APIs, files, network, database touched -- or 'None'>\n"
                    "Tests needed: <Yes if the user asked for tests, verification, or a test "
                    "client/script; No if they only asked for the production code itself>\n\n"
                    "Describe behavior only. Do not describe it in terms of function names, "
                    "classes, or code structure -- the implementation may use as many "
                    "functions as it needs; that's a code-organization detail, not part of the spec."
                ),
            },
            {"role": "user", "content": raw_description},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"].strip()


def extract_external_system(spec: str) -> str:
    """Pull the value of the spec's 'External System called:' line (e.g. 'MySQL', 'AWS', 'None')."""
    match = re.search(r"External System called:\s*(.+)", spec)
    return match.group(1).strip() if match else "None"


# Deterministic fallback for known external systems, keyed by their own name in
# generate.py's *_INSTRUCTION gating (keep this in sync with what's actually
# handled there). The model's own 'External System called:' classification is
# unreliable on this small local model -- it has returned 'None' for a prompt
# that opened with "mySQL database is on the machine" -- so a plain keyword
# match on the user's own words is more trustworthy than its restatement of them.
#
# For AWS specifically, users often name a *service* (EC2, S3, ...) without
# ever saying the word "AWS" itself -- a prompt to "manage EC2 instances,
# S3 instances" never says "AWS" anywhere, so matching only \baws\b missed it
# entirely. "lambda" is deliberately excluded from the service list: it's also
# a Python keyword, and matching it bare would misclassify an ordinary
# "write a lambda function" prompt as an AWS task.
#
# Ollama/LangChain: "local llm"/"tool-calling" catches prompts that never say
# "ollama" literally (e.g. "uses a local LLM with tool-calling" -- the
# 2026-08-13 20260813_182223 run, where DEFINE's own spec named MySQL and
# "internet" but missed the LLM itself entirely, so GENERATE never got any
# LLM-specific guidance and built a keyword-matching dispatcher instead of an
# actual LLM call).
_KNOWN_SYSTEM_KEYWORDS = [
    (re.compile(r"\bmysql\b", re.IGNORECASE), "MySQL"),
    (
        re.compile(
            r"\b(aws|boto3|ec2|s3|dynamodb|sqs|sns|iam|cloudwatch|cloudformation|route\s*53|rds|vpc|ecs|eks)\b",
            re.IGNORECASE,
        ),
        "AWS",
    ),
    (re.compile(r"\bollama\b|\blocal llm\b|\btool[- ]calling\b", re.IGNORECASE), "Ollama"),
    (re.compile(r"\blangchain\b", re.IGNORECASE), "LangChain"),
]


def _keyword_external_systems(raw_description: str) -> list[str]:
    """Scan the user's raw description for every known external-system keyword
    that matches -- a task can genuinely need more than one (e.g. MySQL AND a
    local LLM), so this returns all matches, not just the first."""
    return [name for pattern, name in _KNOWN_SYSTEM_KEYWORDS if pattern.search(raw_description)]


def _apply_external_system_override(spec: str, raw_description: str, logger) -> str:
    """If the raw description clearly names known system(s) the model's own spec
    missed, add them to the spec's 'External System called:' line -- this is
    what actually gates the AWS/MySQL/Ollama/LangChain-specific GENERATE
    instructions, so getting it wrong silently strips all of that guidance.

    Additive, not a wholesale replacement: a spec that already correctly named
    one system (e.g. 'MySQL database, internet') must keep that when a second,
    separately-detected system (e.g. 'Ollama') gets added -- overwriting the
    whole line would silently lose a classification that was already right."""
    matched_systems = _keyword_external_systems(raw_description)
    if not matched_systems:
        return spec

    spec_system = extract_external_system(spec)
    missing = [name for name in matched_systems if name.lower() not in spec_system.lower()]
    if not missing:
        return spec

    if spec_system.strip().lower() in ("", "none"):
        new_value = ", ".join(matched_systems)
    else:
        new_value = spec_system.strip() + ", " + ", ".join(missing)

    logger.info(
        f"External system override: spec said '{spec_system}', but the description "
        f"also mentions {missing} -- using '{new_value}'."
    )
    new_line = f"External System called: {new_value}"
    if re.search(r"External System called:.*", spec):
        return re.sub(r"External System called:.*", new_line, spec, count=1)
    return spec.rstrip() + f"\n{new_line}"


def extract_needs_tests(spec: str) -> bool:
    """Pull the value of the spec's 'Tests needed:' line. Defaults to True (the old,
    always-generate-tests behavior) if the field is missing, e.g. from a spec that
    predates this field."""
    match = re.search(r"Tests needed:\s*(.+)", spec)
    return match.group(1).strip().lower().startswith("yes") if match else True


# Same rationale as _KNOWN_SYSTEM_KEYWORDS/_apply_external_system_override above: this
# model's own 'Tests needed' classification is unreliable -- observed writing 'Tests
# needed: Yes' for prompts (e.g. 20260813_013836, 20260813_012157) that never say the
# word "test" anywhere, doubling generation time and scope for tests nobody asked for.
_TESTS_KEYWORD_RE = re.compile(r"\btest(s|ing)?\b|\bpytest\b|\bunittest\b", re.IGNORECASE)


def _apply_needs_tests_override(spec: str, raw_description: str, logger) -> str:
    """If the raw description's own mention (or lack) of testing disagrees with the
    spec's 'Tests needed' line, rewrite the line to match -- this is what actually
    gates whether GENERATE writes a test file at all, so trusting the model's
    unreliable restatement over the user's own words silently doubles unrequested
    work (or, in the other direction, silently drops tests the user did ask for)."""
    mentions_tests = bool(_TESTS_KEYWORD_RE.search(raw_description))
    spec_says_yes = extract_needs_tests(spec)
    if mentions_tests == spec_says_yes:
        return spec

    correct_value = "Yes" if mentions_tests else "No"
    logger.info(
        f"Tests-needed override: spec said '{'Yes' if spec_says_yes else 'No'}', but the "
        f"description {'mentions' if mentions_tests else 'never mentions'} testing -- "
        f"using '{correct_value}'."
    )
    new_line = f"Tests needed: {correct_value}"
    if re.search(r"Tests needed:.*", spec):
        return re.sub(r"Tests needed:.*", new_line, spec, count=1)
    return spec.rstrip() + f"\n{new_line}"


_FIELD_LABELS = ("Input:", "Output:", "Steps:", "Test Steps:", "External System called:", "Tests needed:")
_NEXT_FIELD_LOOKAHEAD = "|".join(re.escape(label) for label in _FIELD_LABELS)


def extract_test_steps(spec: str) -> str:
    """Pull the value of the spec's 'Test Steps:' section (everything up to the next labeled
    field or end of string). Defaults to a generic fallback if the field is missing, e.g. from
    a spec that predates this field, or the model omitted it despite instructions."""
    match = re.search(rf"Test Steps:\s*(.*?)(?=\n\s*(?:{_NEXT_FIELD_LOOKAHEAD})|\Z)", spec, re.DOTALL)
    text = match.group(1).strip() if match else ""
    return text or "Write thorough unit tests verifying the production code behaves as described."


def strip_test_content(spec: str) -> str:
    """Remove the 'Test Steps:' section and the 'Tests needed:' line entirely from the spec
    text handed to the SOURCE round -- it should see nothing about tests at all, not even a
    field to ignore.

    Regression case: the 2026-08-13 20260813_113104 run, where the source round wrote a full
    test file itself (with its own missing 'import mysql.connector' bug) because the spec's
    Steps section named a test script the source round's own system prompt told it not to
    write -- a concrete instruction sitting in the user message beat an abstract one in the
    system message. Splitting the spec so the source round's input literally contains no test
    content removes the contradiction instead of trying to out-argue it."""
    cleaned = re.sub(
        rf"\n*Test Steps:.*?(?=\n\s*(?:{_NEXT_FIELD_LOOKAHEAD})|\Z)", "\n", spec, flags=re.DOTALL
    )
    cleaned = re.sub(r"\n*Tests needed:.*?(?=\Z)", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def define_task(confirm, logger, is_test: bool = False) -> str:
    """Loop: describe -> restate -> confirm, until the user accepts the spec.

    No attempt cap -- this is a human confirming intent, not an automated repair loop.
    """
    description = input("Describe the code you want generated: ").strip()
    while True:
        logger.info(f"User prompt:\n{description}")
        spec = restate_task(description)
        spec = _apply_external_system_override(spec, description, logger)
        spec = _apply_needs_tests_override(spec, description, logger)
        logger.info(f"Proposed spec:\n{spec}")
        if confirm("Is this correct?"):
            logger.info("Spec confirmed by user.")
            record_confirmed_prompt(description, is_test=is_test)
            return spec
        logger.info("Spec rejected by user; re-prompting for a new description.")
        description = input(
            "Let's try again -- describe what you want (you can reference the spec above): "
        ).strip()
