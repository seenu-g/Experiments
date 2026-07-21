import ast
import json
import operator
import string
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from capture_audio import record_audio
from audio_to_text import ask_llm, speak, transcribe_audio

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


def get_current_time():
    return datetime.now().strftime("%I:%M %p")


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


_WORD_OPERATORS = {
    "plus": "+",
    "minus": "-",
    "times": "*",
    "multiplied by": "*",
    "divided by": "/",
    "x": "*",
    "×": "*",
    "÷": "/",
}

_CALCULATE_ALIASES = {
    "calculate", "add", "plus", "sum",
    "subtract", "minus", "difference",
    "multiply", "times", "product",
    "divide", "quotient",
}


def _normalize_expression(expression):
    normalized = expression.lower()
    for word, symbol in _WORD_OPERATORS.items():
        normalized = normalized.replace(word, symbol)
    return normalized


def calculate(expression):
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except Exception:
        pass

    try:
        tree = ast.parse(_normalize_expression(expression), mode="eval")
        return str(_eval_node(tree.body))
    except Exception:
        return "Unable to calculate the expression."


tools_description = """
                        Available tools:

                        1. get_current_time
                        Use this when the user asks for the current time.

                        2. calculate
                        Use this for mathematical calculations.

                        If a tool is required, respond ONLY with JSON:

                        {
                            "tool": "tool_name",
                            "argument": "tool_argument"
                        }

                        If no tool is required, respond normally.
                        """


def _extract_json_object(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def process_response(response):
    tool_call = _extract_json_object(response)
    if tool_call is None:
        return response

    tool_name = (tool_call.get("tool") or "").strip().lower()
    argument = tool_call.get("argument")

    if tool_name == "get_current_time":
        result = get_current_time()
    elif tool_name in _CALCULATE_ALIASES:
        result = calculate(str(argument))
    else:
        print(f"[debug] Unrecognized tool call: {tool_call}")
        return response

    return f"The result is {result}"


def run_voice_agent():
    while True:
        try:
            record_audio()

            user_text = transcribe_audio()

            print("You:", user_text)

            if not user_text:
                continue

            normalized_text = user_text.lower().strip().strip(string.punctuation)

            if normalized_text in ["exit", "quit", "stop"]:
                print("Voice Agent stopped.")
                break

            llm_response = ask_llm(user_text, tools_description)

            final_response = process_response(llm_response)

            print("Agent:", final_response)

            speak(final_response)
        except Exception as exc:
            print("Error during voice agent loop:", exc)


if __name__ == "__main__":
    run_voice_agent()
