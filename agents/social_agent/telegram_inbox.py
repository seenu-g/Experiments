"""
telegram_inbox.py — Collect tweets you share to your Telegram bot.

    python telegram_inbox.py          # check once and exit (for Windows Task Scheduler)
    python telegram_inbox.py --loop   # keep running; picks up shares within seconds

Needs your bot token and chat id, from either:
    environment variables  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (setx ..., then reopen the terminal;
                           in VS Code, restart VS Code itself), or
    telegram_config.json   next to this file: {"bot_token": "123:ABC...", "chat_id": 123456789}
                           (kept out of git by .gitignore - the token is a password)

Only messages from TELEGRAM_CHAT_ID are used; anyone else is ignored.
Tweet links in a message are collected into this week's folder (collect_tweets.collect),
the week's report is rebuilt, and the bot replies with a short summary.
Telegram keeps undelivered messages for about 24 hours: run this at least daily.
"""

import json
import os
import sys
from datetime import datetime

import requests

import report
import store_tweets
from collect_tweets import collect, extract_urls
from read_tweet import TweetError

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "telegram_state.json")
CONFIG_FILE = os.path.join(HERE, "telegram_config.json")
LOOP_WAIT = 50           # seconds Telegram holds a request open in --loop mode (long polling)


# Call a Bot API method. http_timeout is how long we wait for the reply; Telegram's own
# "timeout" parameter (long polling) is passed through in params.
def api(token: str, method: str, http_timeout: int = 15, **params) -> dict:
    resp = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=http_timeout)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
    return data["result"]


# The last handled update id, so a message is never processed twice (and a crash loses none:
# the offset is saved after each message). Telegram drops updates once we ask past them.
def load_offset() -> int:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)["offset"]
    except (OSError, ValueError, KeyError):
        return 0


def save_offset(offset: int) -> None:
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f)
    os.replace(tmp, STATE_FILE)


# Tweet links in a message: in its text/caption, and in hidden links (text_link entities).
def links_in(message: dict) -> list[str]:
    text = message.get("text") or message.get("caption") or ""
    hidden = [e.get("url", "") for e in message.get("entities", []) + message.get("caption_entities", [])
              if e.get("type") == "text_link"]
    return extract_urls(" ".join([text] + hidden))


# One pass: fetch new messages, collect their tweets, reply once with a summary.
def check_once(token: str, my_chat_id: int, wait: int = 0) -> None:
    updates = api(token, "getUpdates", http_timeout=wait + 15, offset=load_offset(), timeout=wait)
    counts = {"saved": 0, "skipped": 0, "failed": 0, "no link": 0}
    errors = []
    now = datetime.now()

    for update in updates:
        message = update.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id != my_chat_id:
            print(f"Ignored update {update['update_id']} from chat {chat_id}")
        else:
            urls = links_in(message)
            if not urls:
                counts["no link"] += 1
            for url in urls:
                try:
                    counts[collect(url, now)] += 1
                except TweetError as e:
                    counts["failed"] += 1
                    errors.append(str(e))
        save_offset(update["update_id"] + 1)       # handled: never fetch it again

    if not updates:
        return
    path = report.build_report(store_tweets.week_name(now)) if counts["saved"] else None
    summary = ", ".join(f"{k} {v}" for k, v in counts.items() if v) or "nothing new"
    print(f"{now:%Y-%m-%d %H:%M} {summary}" + (f" | report: {path}" if path else ""))
    for error in errors:                           # same reasons as the Telegram reply, for the log
        print(f"  failed: {error}")
    if counts["saved"] or counts["failed"] or counts["no link"]:
        reply = f"Tweets: {summary}." + "".join(f"\n- {e}" for e in errors[:5])
        api(token, "sendMessage", chat_id=my_chat_id, text=reply)


# Token and chat id: environment variables first, then telegram_config.json next to this file.
def load_settings() -> tuple[str | None, str | None]:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)
        token = token or config.get("bot_token")
        chat = chat or config.get("chat_id")
    except FileNotFoundError:
        pass
    except ValueError as e:
        print(f"{CONFIG_FILE} is not valid JSON: {e}", file=sys.stderr)
    return token, (str(chat) if chat else None)


def main(args: list[str]) -> int:
    token, chat = load_settings()
    if not token or not chat:
        missing = " and ".join(n for n, v in [("bot token", token), ("chat id", chat)] if not v)
        print(f"No {missing} found. Set the environment variables or create {CONFIG_FILE} "
              "(see the top of this file).", file=sys.stderr)
        return 1
    loop = "--loop" in args
    if loop:
        print("Waiting for tweets shared to the bot... (Ctrl+C to stop)")
    while True:
        try:
            check_once(token, int(chat), wait=LOOP_WAIT if loop else 0)
        except (requests.RequestException, RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            if not loop:
                return 1
        except KeyboardInterrupt:
            print("Stopped.")
            return 0
        if not loop:
            return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
