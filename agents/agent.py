"""
Shared Agent class used by system_agent.py and report_agent.py.

Same think -> call tool -> observe loop as simple_agent.py, but each agent has
its own name, instructions and tool set.
"""

import json
from datetime import datetime

import ollama

from simple_agent import MODEL, MAX_STEPS, VERBOSE

NUM_CTX = 8192         # Ollama's default context is small; tool results need room
LOG_FILE = "agent_log.txt"


# Record of every question, tool call and answer - for you, never sent to the model.
def log(who: str, text: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {who}: {text}\n")


# A tool raises this to end the agent's run with a fixed message, skipping the extra
# model call that would only repeat the tool result (e.g. "report saved", "user said no").
class StopAgent(Exception):
    pass


class Agent:
    def __init__(self, name: str, instructions: str, tools: list):
        self.name = name
        self.instructions = instructions
        self.tools = tools                          # ollama builds schemas from signatures + docstrings
        self.funcs = {f.__name__: f for f in tools}

    # The model has no memory between calls: every call re-sends `history` (user messages,
    # tool calls, tool results). The caller decides what memory an agent has by what it
    # passes in - a long-lived list gives chat memory, a new list gives none.
    def run(self, history: list) -> str:
        seen = {}                                  # (tool, args) -> call it was first made in
        for step in range(1, MAX_STEPS + 1):       # each pass = one model call
            where = f"call {step}/{MAX_STEPS}"
            # Instructions go in as a leading user message, not role "system": hermes3's Ollama
            # template drops the system message whenever tools are passed ("if .Tools ... else if .System").
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": self.instructions}] + history,
                tools=self.tools,
                options={"num_ctx": NUM_CTX},
            )
            msg = response.message
            history.append(msg)

            # How much the model had to read this call. Near NUM_CTX, Ollama silently drops the
            # oldest tokens - including the system prompt - and the agent starts misbehaving.
            tokens = response.prompt_eval_count or 0
            warn = "  <-- NEAR CONTEXT LIMIT" if tokens > 0.8 * NUM_CTX else ""
            tag = f"[{self.name} {where}, tokens: {tokens}/{NUM_CTX}]"

            if not msg.tool_calls:
                log(tag, f"answer: {msg.content}{warn}")
                if VERBOSE:
                    print(f"  {tag} answer{warn}")
                return msg.content

            for call in msg.tool_calls:
                name = call.function.name
                args = call.function.arguments or {}
                func = self.funcs.get(name)
                try:                               # send bad calls back to the model instead of crashing
                    if isinstance(args, str):
                        args = json.loads(args or "{}")
                    key = (name, json.dumps(args, sort_keys=True))
                    if key in seen:                # loop guard: same call again won't give new data
                        result = (f"LOOP GUARD: you already called {name} with these arguments in "
                                  f"call {seen[key]}; calling again gives the same result. "
                                  "Answer the user now with what you have.")
                    else:
                        seen[key] = step
                        result = func(**args) if func else f"Error: unknown tool '{name}'"
                except StopAgent as stop:          # tool says the job is done - no more model calls
                    log(tag, f"tool {name}({args}) -> {stop} [final, run ended]")
                    if VERBOSE:
                        print(f"  {tag} {name}(...) -> final, no more model calls")
                    history.append({"role": "tool", "content": str(stop), "tool_name": name})
                    return str(stop)
                except Exception as e:
                    result = f"Error calling {name}: {e}"

                first_line = str(result).splitlines()[0] if result else ""
                log(tag, f"tool {name}({args}) -> {first_line}{warn}")
                if VERBOSE:
                    print(f"  {tag} {name}({args}) -> {first_line}{warn}")

                history.append({"role": "tool", "content": str(result), "tool_name": name})

        log(f"[{self.name}]", f"stopped: reached MAX_STEPS ({MAX_STEPS})")
        return "I stopped after too many steps. Try rephrasing your request."
