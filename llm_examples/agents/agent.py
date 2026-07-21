"""
Minimal local agent loop, built from scratch (no LangGraph/MCP).

Shows the core mechanics: send messages + tool schemas to the model,
if it asks to call a tool, run it and feed the result back, repeat
until the model answers in plain text.

Requires Ollama running locally with MODEL pulled (tool-calling capable).
"""

import json
from pathlib import Path

import ollama

from tools import CONFIRM_REQUIRED, TOOLS_BY_NAME, TOOL_SCHEMAS

MODEL = "llama3.1:latest"
HISTORY_FILE = Path(__file__).parent / "history.json"

SYSTEM_PROMPT = (
    "You are a helpful assistant. Only call a tool when one of the available "
    "tools directly applies (e.g. current time, arithmetic). For anything "
    "else, including general knowledge questions, answer directly from what "
    "you know -- do not invent or hypothesize tools that were not provided. "
    "When a tool returns a result, that result is ground truth: report it "
    "verbatim (quote file contents exactly, state the exact time returned) "
    "and never override it with your own prior knowledge, training cutoff, "
    "or guesses."
)


# ---- Agent loop ----------------------------------------------------------

def _default_confirm(name: str, args: dict) -> bool:
    answer = input(f"  [confirm] allow {name}({args})? [y/N]: ")
    return answer.strip().lower() == "y"


def run_agent(user_input: str, history: list[dict], confirm=_default_confirm) -> list[dict]:
    messages = history + [{"role": "user", "content": user_input}]

    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        message = response["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            print(f"\nAssistant: {message['content']}\n")
            return messages

        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            if name in CONFIRM_REQUIRED and not confirm(name, args):
                print(f"  [denied] {name}({args})")
                messages.append(
                    {"role": "tool", "content": f"denied by user: {name} was not executed"}
                )
                continue

            print(f"  [tool call] {name}({args})")
            fn = TOOLS_BY_NAME[name]
            # Tool errors are returned as text, not raised -- the model sees the
            # failure and can decide how to respond, instead of the loop crashing.
            try:
                result = fn(**args)
            except Exception as e:
                result = f"error: {e}"
            print(f"  [tool result] {result!r}")
            messages.append({"role": "tool", "content": str(result)})


def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def save_history(history: list[dict]) -> None:
    # messages from the model are pydantic objects; plain dicts pass through model_dump-less
    plain = [m.model_dump(exclude_none=True) if hasattr(m, "model_dump") else m for m in history]
    HISTORY_FILE.write_text(json.dumps(plain, indent=2))


def main():
    history = load_history()
    print(f"Local agent ready (model={MODEL}). Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        history = run_agent(user_input, history)
        save_history(history)


if __name__ == "__main__":
    main()
