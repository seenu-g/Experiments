"""Local-Ollama-model-specific knowledge: the real ollama package API and the
exact tool-calling loop shape. Kept out of generate.py -- see systems/__init__.py.
"""

from config import LOCAL_MODEL

NAME = "Ollama"


def matches(external_system: str) -> bool:
    return "ollama" in external_system.lower()


NEEDS_CONFIG_FILE = False

SOURCE_INSTRUCTION = (
    "If the task calls a local Ollama model directly (not via LangChain), use the real 'ollama' "
    "package API -- there is no ollama.initialize() function. Use either "
    f"ollama.chat(model='{LOCAL_MODEL}', messages=[{{'role': 'user', 'content': prompt}}])"
    f"['message']['content'], or ollama.generate(model='{LOCAL_MODEL}', prompt=prompt)['response']. "
    f"Always pass the exact, real model name '{LOCAL_MODEL}' -- never a placeholder-looking string "
    "like 'your-model-name' or 'model-name'. Ollama validates the model name against what's actually "
    "installed and raises a 404 ResponseError for anything else, so a made-up name (fine for other "
    "demo arguments) is a real bug here, not just a style choice. If the task requires tool-calling "
    "(the LLM itself deciding which function to invoke), use ollama.chat's 'tools' parameter with a "
    "proper function-calling schema and let the model's own response determine which tool to call -- "
    "do not keyword-match the user's question yourself in plain Python; that is not LLM-driven tool "
    "use, it defeats the point of the task.\n\n"
    "Follow this exact two-call loop -- copy this shape, do not invent your own control flow:\n\n"
    "TOOLS = [\n"
    "    {\n"
    "        'type': 'function',\n"
    "        'function': {\n"
    "            'name': 'get_current_date_time',\n"
    "            'description': 'Get the current date and time. Use this when the question asks "
    "about the current date, time, or day.',\n"
    "            'parameters': {'type': 'object', 'properties': {}, 'required': []},\n"
    "        },\n"
    "    },\n"
    "    # one dict per tool, same shape, with real 'properties' for any arguments it takes\n"
    "]\n"
    "TOOL_REGISTRY = {'get_current_date_time': get_current_date_time, ...}  # name -> real Python function\n\n"
    "def ask_agent(question):\n"
    "    messages = [{'role': 'user', 'content': question}]\n"
    "    first = ollama.chat(model='" + LOCAL_MODEL + "', messages=messages, tools=TOOLS)\n"
    "    reply = first['message']\n"
    "    tool_calls = reply.get('tool_calls')\n"
    "    if not tool_calls:\n"
    "        return reply['content']  # model answered directly, no tool was needed\n"
    "    messages.append(reply)\n"
    "    for call in tool_calls:\n"
    "        name = call['function']['name']\n"
    "        args = call['function']['arguments']  # already a dict, do not json.loads it\n"
    "        result = TOOL_REGISTRY[name](**args)\n"
    "        messages.append({'role': 'tool', 'content': str(result), 'name': name})\n"
    "    second = ollama.chat(model='" + LOCAL_MODEL + "', messages=messages, tools=TOOLS)\n"
    "    return second['message']['content']\n\n"
    "Never call a tool function directly from your own Python logic based on keywords found in the "
    "question -- the ONLY thing allowed to decide which tool(s) run is the 'tool_calls' the model "
    "returns from the first ollama.chat call above. In __main__, call ask_agent() with at least two "
    "different example questions, chosen so each one should naturally route to a different tool -- "
    "this is what actually demonstrates tool selection; one question that happens to need every tool "
    "proves nothing about whether the model, rather than your code, made the choice."
)

TEST_INSTRUCTION = None

AUTOFIXES = []
