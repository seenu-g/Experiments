"""
client.py — Interactive terminal chat with the HR agent.

Run:  python client.py

Type your question in plain English. Type 'reset' to clear history, 'quit' to exit.
Ctrl+C while the agent is working cancels that question; Ctrl+C at the prompt exits.
Errors (Ollama down, model missing, ...) are explained and the chat continues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import ollama

from hr_agent import HRAgent, MODEL
from logger import log

BANNER = """
╔══════════════════════════════════════════════╗
║         HR Agent  •  Ollama + Hermes         ║
║         Local • PostgreSQL • No API key      ║
╠══════════════════════════════════════════════╣
║  Try:                                        ║
║  • List all managers                         ║
║  • Show salary of managers in Engineering    ║
║  • What is the education of Sarah Johnson?   ║
║  • Disable employee John Smith               ║
║  • How many active employees per department? ║
║  Type 'reset' to clear history, 'quit' exit  ║
╚══════════════════════════════════════════════╝
"""

TABLE_MAX_ROWS = 20      # rows printed per result; the rest are counted
TABLE_MAX_WIDTH = 40     # longest value shown per column


# Print database rows as a table - by code, so the numbers on screen are the real ones.
def print_table(rows: list[dict]) -> None:
    cols = list(rows[0])
    shown = rows[:TABLE_MAX_ROWS]
    width = {c: min(TABLE_MAX_WIDTH, max([len(c)] + [len(str(r.get(c, ""))) for r in shown])) for c in cols}
    print("    " + "  ".join(c.ljust(width[c]) for c in cols))
    print("    " + "  ".join("-" * width[c] for c in cols))
    for r in shown:
        print("    " + "  ".join(str(r.get(c, ""))[:width[c]].ljust(width[c]) for c in cols))
    if len(rows) > TABLE_MAX_ROWS:
        print(f"    ... {len(rows) - TABLE_MAX_ROWS} more rows")


# What to tell the user for each kind of failure. The agent has already dropped the failed
# turn from its history, so the chat can simply continue.
def explain(error: BaseException) -> str:
    if isinstance(error, KeyboardInterrupt):
        return "Cancelled. That question was dropped - ask again, or type 'quit' to exit."
    if isinstance(error, ConnectionError):
        return "Cannot reach Ollama. Start it (open the Ollama app, or run `ollama serve`), then ask again."
    if isinstance(error, ollama.ResponseError):
        if error.status_code == 404:
            return f"Model '{MODEL}' is not installed. Run `ollama pull {MODEL}`, or change MODEL in hr_agent.py."
        return f"Ollama returned an error: {error.error}. Try again; if it repeats, restart Ollama."
    return f"Unexpected error ({type(error).__name__}: {error}). That question was dropped; you can keep chatting."


def main():
    print(BANNER)
    agent = HRAgent()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Bye!")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print("✓ Conversation history cleared.")
            continue

        print()
        try:
            show_turn(agent, user_input)
        except (Exception, KeyboardInterrupt) as e:  # never crash: explain, then back to the prompt
            log("[client error]", f"{type(e).__name__}: {e}")
            print(f"\n⚠️  {explain(e)}")


def show_turn(agent: HRAgent, user_input: str) -> None:
    for event in agent.steps(user_input):
        if event["type"] == "tool" and event.get("query"):
            # Full SQL, unindented, so it can be copied as-is into pgAdmin / psql to verify
            print(f"    🔧 {event['name']} — SQL written by the model:\n")
            print(event["query"].strip().rstrip(";") + ";\n")
        elif event["type"] == "tool":
            print(f"    🔧 {event['name']}({event['args']})")
        elif event["type"] == "result":
            print(f"    📦 {event['data']}")
        elif event["type"] == "rows":
            print("\n    Data from database:")
            print_table(event["data"])
            print()
        else:
            print(f"Agent (model's summary): {event['data']}")


if __name__ == "__main__":
    main()
