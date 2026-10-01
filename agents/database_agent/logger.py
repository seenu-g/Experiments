"""
logger.py — Log file for the HR agent (CLI and API).

One line per event:
    [2026-09-30 19:26:46] [hr-agent call 2/10, tokens: 1277/8192]: answer: ...

The log goes next to this file (database_agent/agent_log.txt), so the CLI and the API
write to the same log no matter which folder they are started from.
"""

import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_log.txt")


def log(who: str, text: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {who}: {text}\n")
