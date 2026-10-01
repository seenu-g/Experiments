"""
history.py — What the model gets to see from earlier turns (context engineering).

The model has no memory: it only reads what the app sends. So the app decides, after
every turn, what stays in the history the model will see next time:

  kept      - user questions and the model's answers (last MAX_TURNS), so "her" or
              "the second one" can still be understood
  kept      - the fact that a tool was called, so the model keeps the habit of calling tools
  replaced  - old tool results: they are stale snapshots, and a model that sees them answers
              from them (or reuses ids from them) instead of asking the database again
  dropped   - turns older than MAX_TURNS, so the prompt stays small

Instructions and schema are not in the history: hr_agent.py adds them fresh on every call.
"""

MAX_TURNS = 5
STALE_RESULT = "[old result removed - data may have changed; call the tool again for current data]"


def hide_old_tool_results(history: list, start: int) -> None:
    for i in range(start, len(history)):
        if history[i].get("role") == "tool":
            history[i] = {"role": "tool", "content": STALE_RESULT, "tool_name": history[i].get("tool_name")}


# Cut at a user message, so a tool call is never separated from its result.
def keep_last_turns(history: list) -> None:
    user_idx = [i for i, m in enumerate(history) if m.get("role") == "user"]
    if len(user_idx) > MAX_TURNS:
        del history[:user_idx[-MAX_TURNS]]


# Called by the app after each finished turn; `start` is where that turn began in the history.
def curate(history: list, start: int) -> None:
    hide_old_tool_results(history, start)
    keep_last_turns(history)
