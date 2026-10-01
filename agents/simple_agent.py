"""
Simple local agent: Ollama + Hermes with tool calling.

Setup:
    pip install ollama
    ollama pull hermes3        # skip if you already have it
    python simple_agent.py

Change MODEL below if your Hermes model has a different name (check: `ollama list`).
"""

import ast
import json
import operator
import os
from datetime import datetime

import ollama

MODEL = "hermes3"
MAX_STEPS = 6          # stops the agent from looping forever
NOTES_FILE = "agent_notes.txt"
VERBOSE = True         # prints each tool call so you can watch the agent think


# ---------------------------------------------------------------------------
# 1. TOOLS — plain Python functions the agent can call
# ---------------------------------------------------------------------------

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}
MAX_EXPONENT = 1000    # blocks things like 9**9**9 that would hang the process


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError(f"Exponent too large (max {MAX_EXPONENT})")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Only numbers and + - * / ** % are allowed")


def calculator(expression: str) -> str:
    """Evaluate a math expression like '1200 * 0.18 + 50'."""
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


def get_current_time() -> str:
    """Return the current local date and time."""
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")


def save_note(text: str) -> str:
    """Append a note to a local file."""
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{get_current_time()}] {text}\n")
    return "Note saved."


def read_notes() -> str:
    """Read all saved notes."""
    if not os.path.exists(NOTES_FILE):
        return "No notes yet."
    with open(NOTES_FILE, encoding="utf-8") as f:
        return f.read() or "No notes yet."


TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "save_note": save_note,
    "read_notes": read_notes,
}

# ---------------------------------------------------------------------------
# 2. TOOL SCHEMAS — how the model learns what each tool does
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Do exact arithmetic. Use for ANY calculation instead of guessing.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "e.g. '2500 * 12 * 0.07'"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get today's date and the current time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a note or reminder the user wants to keep.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_notes",
            "description": "Read the user's saved notes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = (
    "You are a helpful assistant with tools. "
    "Use the calculator for every calculation, never do math in your head. "
    "Use tools only when needed; otherwise answer directly. "
    "After getting tool results, give the user a short, clear answer."
)


# ---------------------------------------------------------------------------
# 3. THE AGENT LOOP — think -> call tool -> observe -> repeat -> answer
# ---------------------------------------------------------------------------

def run_agent(messages: list) -> str:
    for step in range(MAX_STEPS):
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        msg = response.message
        messages.append(msg)

        if not msg.tool_calls:                     # no tool needed -> final answer
            return msg.content

        for call in msg.tool_calls:                # run every tool the model asked for
            name = call.function.name
            args = call.function.arguments or {}
            func = TOOLS.get(name)
            try:                                   # send bad calls back to the model instead of crashing
                if isinstance(args, str):
                    args = json.loads(args or "{}")
                result = func(**args) if func else f"Error: unknown tool '{name}'"
            except Exception as e:
                result = f"Error calling {name}: {e}"

            if VERBOSE:
                print(f"  [tool] {name}({args}) -> {result}")

            messages.append({"role": "tool", "content": str(result), "tool_name": name})

    return "I stopped after too many steps. Try rephrasing your request."


def main():
    print(f"Local agent using '{MODEL}'. Type 'exit' to quit.\n")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue
        checkpoint = len(messages)
        messages.append({"role": "user", "content": user})
        try:
            print(f"Agent: {run_agent(messages)}\n")
        except ollama.ResponseError as e:
            del messages[checkpoint:]              # drop the half-finished turn so history stays valid
            print(f"Ollama error: {e}\n(Check the model name with `ollama list`.)\n")


if __name__ == "__main__":
    main()
