"""
hr_agent.py — HR Agent core: Hermes + Ollama tool-calling loop.

Handles natural language questions about employees, salaries, departments.
Also handles the disable-employee write operation with a confirmation step
that is enforced in code, not left to the model.

Used by both client.py (terminal) and hr_api.py (FastAPI).
"""

import json
import time

import ollama
from logger import log
from db_tools import run_tool, confirm_disable
from history import curate
from instructions import SYSTEM_PROMPT
from tool_definitions import TOOL_DEFINITIONS

MODEL = "hermes3"
MAX_ITERATIONS = 10
NUM_CTX = 8192                                     # context window; shown as tokens: n/NUM_CTX
LOG_RESULT_MAX = 5000                              # raw tool result chars written to the log

YES = {"yes", "y"}
NO = {"no", "n"}


class HRAgent:
    # name appears in every log line; the API passes "hr-agent:<session_id>" so sessions can be told apart
    def __init__(self, name: str = "hr-agent"):
        self.name = name
        self.history: list[dict] = []
        self.pending: dict | None = None           # disable request waiting for the user's yes/no

    def reset(self):
        self.history = []
        self.pending = None

    def chat(self, user_message: str) -> str:
        """Run one turn and return only the final answer."""
        answer = ""
        for event in self.steps(user_message):
            if event["type"] == "answer":
                answer = event["data"]
        return answer

    # One user turn as a stream of events, so the CLI can print them and the API can
    # return or stream them:  {"type": "tool", "name", "args", "query"}  {"type": "result", "data"}
    #                         {"type": "rows", "data": [dict, ...]}  - raw rows from the database
    #                         {"type": "answer", "data"}  - always the last event
    # After the turn, the app curates what the model will see next time (history.py).
    def steps(self, user_message: str):
        start = len(self.history)
        try:
            yield from self._turn(user_message)
        except (Exception, KeyboardInterrupt):     # Ctrl+C mid-turn too
            del self.history[start:]               # failed turn: drop it, never leave half a turn behind
            raise
        finally:
            curate(self.history, start)

    def _turn(self, user_message: str):
        log(f"user [{self.name}]", user_message)
        if self.pending:
            decision = self._resolve_pending(user_message)
            if decision is not None:
                yield {"type": "answer", "data": decision}
                return

        self.history.append({"role": "user", "content": user_message})
        # Not role "system": hermes3's Ollama template drops the system message whenever tools are
        # passed ("if .Tools ... else if .System"), so the model never saw the schema and invented
        # tables like "employees". A leading user message is always included.
        messages = [{"role": "user", "content": SYSTEM_PROMPT}] + self.history

        for iteration in range(1, MAX_ITERATIONS + 1):
            response = ollama.chat(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                options={"num_ctx": NUM_CTX},
            )

            msg = response["message"]
            self.history.append(msg)
            messages.append(msg)

            # tokens = what the model had to read this call (history + tool results)
            tokens = response.get("prompt_eval_count") or 0
            # Model time as measured by Ollama (nanoseconds). Load time is shown only when it
            # matters: it means the model had to be loaded into memory before answering.
            took, load = (response.get("total_duration") or 0) / 1e9, (response.get("load_duration") or 0) / 1e9
            loaded = f" (load {load:.1f}s)" if load >= 1 else ""
            tag = f"[{self.name} call {iteration}/{MAX_ITERATIONS}, tokens: {tokens}/{NUM_CTX}, time: {took:.1f}s{loaded}]"

            # No tool calls → this is the final text answer
            if not msg.get("tool_calls"):
                answer = (msg.get("content") or "").strip()
                log(tag, f"answer: {answer}")
                yield {"type": "answer", "data": answer}
                return

            # Execute each tool call and feed results back
            for tc in msg["tool_calls"]:
                fn       = tc["function"]
                name     = fn["name"]
                raw_args = fn["arguments"]
                args     = raw_args if isinstance(raw_args, dict) else json.loads(raw_args)

                # Two log lines, because two different actors are involved:
                #   model line - what the model asked for (full args, so a bad query can be diagnosed)
                #   app line   - what our code did with it, and how long it took
                log(tag, f"model requested {name}({json.dumps(args)})")
                yield {"type": "tool", "name": name, "args": _preview(args), "query": args.get("query")}
                started = time.perf_counter()
                result = run_tool(name, args)
                # The raw result goes back to the model, which rewrites it as the answer you see.
                # Its size shows up in the next call's token count.
                log(f"[{self.name} app]", f"ran {name} in {time.perf_counter() - started:.2f}s "
                                          f"-> {_preview_result(result)}; sending {len(result)} chars to model")
                # Raw result too, so the model's answer can be checked against the real data.
                extra = f" ... ({len(result)} chars total)" if len(result) > LOG_RESULT_MAX else ""
                log(f"[{self.name} app]", f"{name} result: {result[:LOG_RESULT_MAX]}{extra}")
                yield {"type": "result", "data": _preview_result(result)}

                # The rows themselves, straight from the database - the CLI prints them by code,
                # so what you see is the real data, not the model's retelling of it.
                data = _parse(result)
                rows = data.get("rows") or data.get("matches")
                if rows:
                    yield {"type": "rows", "data": rows}

                tool_msg = {"role": "tool", "content": result, "tool_name": name}
                messages.append(tool_msg)
                self.history.append(tool_msg)

                # A write was requested: stop here and ask the user. No model call is spent
                # on phrasing the question, and the model never decides whether it happens.
                request = _parse(result)
                if request.get("confirmation_required"):
                    self.pending = {"emp_id": request["emp_id"], "full_name": request["full_name"]}
                    self.history.append({"role": "assistant", "content": request["message"]})
                    log(tag, f"waiting for user confirmation: {request['message']}")
                    yield {"type": "answer", "data": request["message"]}
                    return

        log(f"[{self.name}]", f"stopped: reached MAX_ITERATIONS ({MAX_ITERATIONS})")
        yield {"type": "answer", "data": "I wasn't able to complete that request. Please try rephrasing."}

    # Handle the reply to a pending disable request in code. Returns the answer, or None if the
    # user moved on to something else (the request is then dropped and the model handles the message).
    def _resolve_pending(self, user_message: str) -> str | None:
        pending, self.pending = self.pending, None
        reply = user_message.strip().lower()
        if reply in YES:
            answer = _parse(confirm_disable(pending["emp_id"]))
            answer = answer.get("message") or answer.get("error", "Unknown result.")
        elif reply in NO:
            answer = f"Cancelled — {pending['full_name']} was not disabled."
        else:
            log(f"[{self.name} code]", f"pending disable of emp_id={pending['emp_id']} dropped: reply was not yes/no")
            return None
        log(f"[{self.name} code, no model call]", f"reply '{reply}' to disable emp_id={pending['emp_id']} -> {answer}")
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": answer})
        return answer


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse(result: str) -> dict:
    try:
        data = json.loads(result)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}

def _preview(args: dict) -> str:
    s = json.dumps(args)
    return s[:120] + "..." if len(s) > 120 else s

def _preview_result(result: str) -> str:
    try:
        data = json.loads(result)
        if "rows" in data:
            return f"{data['count']} row(s) returned"
        if "matches" in data:
            return f"{data['count']} match(es) found"
        return result[:150]
    except Exception:
        return result[:150]
