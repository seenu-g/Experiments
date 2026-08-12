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
                    "Restate the user's coding request as a spec using exactly these four "
                    "labeled sections, plain text, no code, no preamble:\n\n"
                    "Input: <what data/values come in>\n"
                    "Output: <what is produced/returned>\n"
                    "Steps: <ordered list of the algorithm-level logic>\n"
                    "External System called: <APIs, files, network, database touched -- or 'None'>\n\n"
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


def define_task(confirm, logger, is_test: bool = False) -> str:
    """Loop: describe -> restate -> confirm, until the user accepts the spec.

    No attempt cap -- this is a human confirming intent, not an automated repair loop.
    """
    description = input("Describe the code you want generated: ").strip()
    while True:
        logger.info(f"User prompt:\n{description}")
        spec = restate_task(description)
        logger.info(f"Proposed spec:\n{spec}")
        if confirm("Is this correct?"):
            logger.info("Spec confirmed by user.")
            record_confirmed_prompt(description, is_test=is_test)
            return spec
        logger.info("Spec rejected by user; re-prompting for a new description.")
        description = input(
            "Let's try again -- describe what you want (you can reference the spec above): "
        ).strip()
