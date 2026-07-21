"""
Minimal local agent loop, built from scratch (no LangGraph/MCP).

Shows the core mechanics: send messages + tool schemas to the model,
if it asks to call a tool, run it and feed the result back, repeat
until the model answers in plain text.

Requires Ollama running locally with MODEL pulled (tool-calling capable).
"""

import ast
import operator
from datetime import datetime

import ollama

MODEL = "llama3.1:latest"

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use tools when they would give a more "
    "accurate answer than guessing (e.g. current time, arithmetic)."
)


# ---- Tools -------------------------------------------------------------
# Each tool is a plain Python function plus a JSON schema describing it.
# The schema is what the model actually sees; the function is what runs.

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate(expression: str) -> str:
    """Safely evaluate a numeric expression (no eval())."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except Exception as e:
        return f"error: {e}"


TOOLS_BY_NAME = {
    "get_current_time": get_current_time,
    "calculate": calculate,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a numeric expression, e.g. '12 * (3 + 4)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "A numeric expression"},
                },
                "required": ["expression"],
            },
        },
    },
]


# ---- Agent loop ----------------------------------------------------------

def run_agent(user_input: str, history: list[dict]) -> list[dict]:
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
            print(f"  [tool call] {name}({args})")
            fn = TOOLS_BY_NAME[name]
            result = fn(**args)
            messages.append({"role": "tool", "content": str(result)})


def main():
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Local agent ready (model={MODEL}). Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        history = run_agent(user_input, history)


if __name__ == "__main__":
    main()
