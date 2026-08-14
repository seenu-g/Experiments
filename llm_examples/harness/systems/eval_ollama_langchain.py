"""Eval for systems/ollama.py and systems/langchain.py's prompt instructions.
Kept in one file (not split) because the real regression this guards is about
their INTERACTION -- both must be able to apply to the same task at once (a
LangChain-mentioning description also implies Ollama underneath).

Run (from the harness/ directory): python -m systems.eval_ollama_langchain
"""

import sys

from generate import build_source_system_instruction
from systems.langchain import SOURCE_INSTRUCTION as LANGCHAIN_INSTRUCTION
from systems.ollama import SOURCE_INSTRUCTION as OLLAMA_INSTRUCTION


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def eval_ollama_and_langchain_instructions():
    """Regression check for the 2026-08-13 20260813_181809/20260813_182028 runs: the model
    hallucinated a nonexistent ollama.initialize() function and a nonexistent
    langchain.LangChainClient class, identically, 3 attempts in a row -- DEFINE correctly
    classified the external system in both runs, but GENERATE had no corresponding
    instruction the way it does for AWS/MySQL, so the model had nothing to ground it and
    just guessed. systems.ollama/systems.langchain's SOURCE_INSTRUCTION close that gap the
    same way AWS/MySQL's already do for their systems."""
    ok = True

    ollama_source = build_source_system_instruction(external_system="Ollama")
    ok &= check(
        "Ollama instruction included when external_system mentions Ollama",
        OLLAMA_INSTRUCTION in ollama_source,
        ollama_source,
    )
    ok &= check(
        "instruction names the real ollama.chat/ollama.generate API, not a guess",
        "ollama.chat(" in ollama_source and "ollama.generate(" in ollama_source,
        ollama_source,
    )
    ok &= check(
        "instruction explicitly says there is no ollama.initialize()",
        "ollama.initialize()" in ollama_source,
        ollama_source,
    )
    ok &= check(
        "instruction tells the model to actually let the LLM pick the tool, not keyword-match it",
        "keyword-match" in ollama_source.lower(),
        ollama_source,
    )
    ok &= check(
        "LangChain instruction excluded when external_system doesn't mention langchain",
        LANGCHAIN_INSTRUCTION not in ollama_source,
        ollama_source,
    )

    langchain_source = build_source_system_instruction(external_system="Local Ollama model via LangChain")
    ok &= check(
        "LangChain instruction included when external_system mentions LangChain",
        LANGCHAIN_INSTRUCTION in langchain_source,
        langchain_source,
    )
    ok &= check(
        "instruction names the real langchain_ollama.OllamaLLM API, not a guess",
        "langchain_ollama" in langchain_source and "OllamaLLM" in langchain_source,
        langchain_source,
    )
    ok &= check(
        "instruction explicitly says there is no langchain.LangChainClient",
        "LangChainClient" in langchain_source,
        langchain_source,
    )
    ok &= check(
        "Ollama instruction also included when external_system mentions LangChain (both can apply)",
        OLLAMA_INSTRUCTION in langchain_source,
        langchain_source,
    )

    neither_source = build_source_system_instruction(external_system="MySQL")
    ok &= check(
        "neither instruction appears for an unrelated external system",
        OLLAMA_INSTRUCTION not in neither_source and LANGCHAIN_INSTRUCTION not in neither_source,
        neither_source,
    )

    return ok


if __name__ == "__main__":
    results = [
        eval_ollama_and_langchain_instructions(),
    ]
    sys.exit(0 if all(results) else 1)
