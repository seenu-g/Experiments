"""
Two local agents working together: Ollama + Hermes with tool calling.

    system_agent.py  - chat agent; looks up system info, installed software and services.
                       Keeps chat memory across turns.
    report_agent.py  - receives ONLY the output of those 3 system tools (REQUIRE_REPORT) and
                       writes the HTML report. Runs only if you said yes to saving. No memory.
    agent.py         - the shared Agent class (tool-calling loop) and log file.
    multi_agent.py   - this file: the orchestrator that decides when to hand off.

Setup:
    pip install ollama psutil
    python multi_agent.py

Try: "what's installed on this machine?"  or  "show me the running services"
"""

import os

import ollama

from agent import LOG_FILE, log
from report_agent import REPORT_AGENT, ask_save_location, handoff_message
from simple_agent import MODEL
from system_agent import REQUIRE_REPORT, SYSTEM_AGENT


# Chat memory keeps the conversation AND the fact that tools were called, but not old results.
# - Old results are stale snapshots; if kept, the model answers from them instead of calling
#   the tool again (e.g. "ssh-agent?" answered from a 15-row services preview).
# - The tool calls must stay: if history only shows "question -> direct answer", a small model
#   copies that pattern and stops calling tools, then invents answers.
STALE_RESULT = "[old result removed - the machine may have changed; call the tool again for current data]"


MAX_TURNS = 5          # chat memory = only the last 5 questions (a sliding window)


def hide_old_tool_results(history: list, start: int) -> None:
    for i in range(start, len(history)):
        if history[i].get("role") == "tool":
            history[i] = {"role": "tool", "content": STALE_RESULT, "tool_name": history[i].get("tool_name")}


# Cut at a user message so a tool call is never separated from its result.
def keep_last_turns(history: list) -> None:
    user_idx = [i for i, m in enumerate(history) if m.get("role") == "user"]
    if len(user_idx) > MAX_TURNS:
        del history[:user_idx[-MAX_TURNS]]


# Plain code, not a model, decides when the report agent runs.
def main():
    print(f"Multi-agent demo using '{MODEL}'. Type 'exit' to quit.")
    print(f"Log: {os.path.abspath(LOG_FILE)}\n")
    log("session", "started")                      # shows restarts in the log
    history = []                                   # system agent: chat memory across turns
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue

        REQUIRE_REPORT.clear()
        log("user", user)
        checkpoint = len(history)
        history.append({"role": "user", "content": user})
        try:
            print(f"{SYSTEM_AGENT.name}: {SYSTEM_AGENT.run(history)}\n")
            hide_old_tool_results(history, checkpoint)
            keep_last_turns(history)
        except ollama.ResponseError as e:
            del history[checkpoint:]               # drop the half-finished turn so history stays valid
            log("error", str(e))
            print(f"Ollama error: {e}\n(Check the model name with `ollama list`.)\n")
            continue

        # Hand-off: only when one of the 3 system tools ran this turn AND the user wants a report.
        # Both checks are plain code - no model call is spent deciding either.
        # Report agent: no memory - a brand-new list every time, it never sees the chat.
        if REQUIRE_REPORT:
            if not ask_save_location():
                log("handoff", f"skipped by user: {', '.join(REQUIRE_REPORT)}")
                print("  [report] skipped - report agent not called.\n")
                continue
            print(f"--- handing {', '.join(REQUIRE_REPORT)} to {REPORT_AGENT.name} ---")
            log("handoff", ", ".join(REQUIRE_REPORT))
            try:
                print(f"{REPORT_AGENT.name}: {REPORT_AGENT.run([{'role': 'user', 'content': handoff_message()}])}\n")
            except ollama.ResponseError as e:
                log("error", str(e))
                print(f"Ollama error in report agent: {e}\n")


if __name__ == "__main__":
    main()
