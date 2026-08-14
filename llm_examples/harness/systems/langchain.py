"""LangChain-specific knowledge: the real langchain_ollama package API. Kept out
of generate.py -- see systems/__init__.py.
"""

from config import LOCAL_MODEL

NAME = "LangChain"


def matches(external_system: str) -> bool:
    return "langchain" in external_system.lower()


NEEDS_CONFIG_FILE = False

SOURCE_INSTRUCTION = (
    "If the task calls a local Ollama model via LangChain, use the real langchain_ollama package -- "
    "there is no langchain.LangChainClient class. Use 'from langchain_ollama import OllamaLLM', then "
    f"'llm = OllamaLLM(model=\"{LOCAL_MODEL}\")' and 'response = llm.invoke(prompt)'. Always pass the "
    f"exact, real model name '{LOCAL_MODEL}' -- never a placeholder-looking string."
)

TEST_INSTRUCTION = None

AUTOFIXES = []
