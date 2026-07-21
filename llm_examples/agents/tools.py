"""
Tools available to the agent: each is a plain Python function plus a JSON
schema describing it. The schema is what the model sees; the function is
what actually runs.
"""

import ast
import operator
import os
from datetime import datetime
from pathlib import Path


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


def read_file(path: str) -> str:
    """Read a text file's contents. Can fail (missing file, permissions, etc)."""
    try:
        return Path(path).read_text()[:2000]
    except FileNotFoundError:
        return f"error: no file found at '{path}'"
    except PermissionError:
        return f"error: no permission to read '{path}'"
    except IsADirectoryError:
        return f"error: '{path}' is a directory, not a file"
    except Exception as e:
        return f"error: {e}"


def delete_file(path: str) -> str:
    """Delete a file. Destructive -- gated behind user confirmation in the loop."""
    try:
        os.remove(path)
        return f"deleted {path}"
    except FileNotFoundError:
        return f"error: no file found at '{path}'"
    except PermissionError:
        return f"error: no permission to delete '{path}'"
    except IsADirectoryError:
        return f"error: '{path}' is a directory, not a file"
    except Exception as e:
        return f"error: {e}"


TOOLS_BY_NAME = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "read_file": read_file,
    "delete_file": delete_file,
}

# Tools that must be confirmed by the human before they run.
CONFIRM_REQUIRED = {"delete_file"}

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
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file at the given path. Destructive: requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to delete"},
                },
                "required": ["path"],
            },
        },
    },
]
