"""GENERATE stage: ask the model for code and parse its reply into file contents.

Parsing is decoupled from writing -- this module never touches disk. SAVE owns
that, so every attempt (pass or fail) can be persisted under a versioned name.
"""

import re

import ollama

from config import LOCAL_MODEL

FILE_HEADER_RE = re.compile(r"^#\s*===\s*FILE:\s*(?P<fname>\S+)\s*===\s*$", re.MULTILINE)
ENTRY_MARKER_RE = re.compile(r"^[ \t]*#\s*===\s*ENTRYPOINT\s*===\s*$\n?", re.MULTILINE)
FENCE_RE = re.compile(r"```\w*\s*\n?(?P<code>.*?)```", re.DOTALL)


def _strip_fence(block: str) -> str:
    """Return the code inside a ```...``` fence if present, else the block as-is.

    The model doesn't always fence its code despite instructions, so a fence
    is treated as optional rather than required.
    """
    fence_match = FENCE_RE.search(block)
    return fence_match.group("code").strip() if fence_match else block.strip()


AWS_INSTRUCTION = (
    "If the task involves AWS services via boto3, write production code with plain boto3 clients "
    "(no hardcoded endpoint_url). For the unit test file, mock AWS with moto: decorate test "
    "functions/classes with @moto.mock_aws (import via 'from moto import mock_aws'), and create "
    "boto3 clients/resources inside the mocked test using region_name='us-east-1' -- moto "
    "intercepts the calls in-process, so no real AWS credentials or network access are needed. "
    "If the task's entrypoint is the test file, running it under moto must fully succeed without "
    "touching real AWS."
)


def build_system_instruction(error_context: str = "", external_system: str = "") -> str:
    system_instruction = (
        "You are an expert Python software engineer. Your task is to output ONLY valid, "
        "executable Python code, with no conversational preamble, explanations, or commentary. "
        "Every 'import' statement required by any function, class, or standard-library call you use "
        "must be included at the top of its file. Never reference a module or name without importing it first.\n\n"
        "This script will be run non-interactively with no terminal attached. Never call 'input()' "
        "or otherwise wait on interactive/stdin input. Demonstrate the code with hardcoded example "
        "arguments under 'if __name__ == \"__main__\":'.\n\n"
        "If the task can be done in a single file, output exactly one ```python ... ``` block.\n\n"
        "If the task explicitly requires multiple files (e.g. one module imported by another), output "
        "one ```python ... ``` block per file, and immediately BEFORE each block put a line in exactly "
        "this form:\n"
        "# === FILE: <filename.py> ===\n"
        "All files you output will be saved together in the same folder, so a plain "
        "'import <filename_without_.py>' between them will resolve correctly. Put the file that should "
        "be run directly (the one with 'if __name__ == \"__main__\":') LAST, and mark the line right "
        "after its FILE header with:\n"
        "# === ENTRYPOINT ===\n"
        "Do not use this multi-file format unless the task genuinely requires more than one file."
    )

    if "aws" in external_system.lower():
        system_instruction += "\n\n" + AWS_INSTRUCTION

    if error_context:
        system_instruction += f"\n\nCRITICAL: Your previous code failed. Completely fix this:\n{error_context}"

    return system_instruction


def ask_local_model_for_code(spec: str, error_context: str = "", external_system: str = "") -> str:
    system_instruction = build_system_instruction(error_context, external_system)

    print(f"Querying {LOCAL_MODEL}...")
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": spec},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"]


def parse_generated_files(raw_llm_text: str, default_filename: str) -> tuple[list, str]:
    """Extract file(s) from the model's reply.

    Returns (files, entry_filename) where files is a list of (filename, code) tuples
    and entry_filename names which of those should be executed. Nothing is written
    to disk here -- SAVE does that with version-numbered filenames.
    """
    clean_text = re.sub(r"<think>.*?</think>", "", raw_llm_text, flags=re.DOTALL)

    headers = list(FILE_HEADER_RE.finditer(clean_text))

    if not headers:
        code = ENTRY_MARKER_RE.sub("", clean_text)
        return [(default_filename, _strip_fence(code))], default_filename

    files = []
    entry_filename = None
    for i, header in enumerate(headers):
        fname = header.group("fname")
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(clean_text)
        block = clean_text[start:end]

        if ENTRY_MARKER_RE.search(block):
            entry_filename = fname
            block = ENTRY_MARKER_RE.sub("", block)

        files.append((fname, _strip_fence(block)))

    return files, entry_filename or files[-1][0]
