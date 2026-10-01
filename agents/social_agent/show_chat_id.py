"""
show_chat_id.py — One-time helper: shows the chat ID of whoever messaged your bot.

Before running:
  1. TELEGRAM_BOT_TOKEN is set (setx TELEGRAM_BOT_TOKEN "...", then reopen PowerShell)
  2. You opened your bot in Telegram, pressed Start, and sent it any message, e.g. "hello"

Run:  python show_chat_id.py
"""

import os
import sys

import requests

token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("TELEGRAM_BOT_TOKEN is not set. Run: setx TELEGRAM_BOT_TOKEN \"<token>\" and reopen PowerShell.")

try:
    data = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15).json()
except requests.RequestException as e:
    sys.exit(f"Could not reach Telegram: {e}")

if not data.get("ok"):
    sys.exit(f"Telegram refused the request: {data.get('description')} - check the token from BotFather.")

messages = [u["message"] for u in data["result"] if "message" in u]
if not messages:
    sys.exit("No messages found. Open your bot in Telegram, send it 'hello', then run this again.")

seen = set()
for m in messages:
    chat_id = m["chat"]["id"]
    if chat_id not in seen:
        seen.add(chat_id)
        print(f"Chat ID {chat_id}  <- from {m['from'].get('first_name', '?')}, message: {m.get('text', '')!r}")

print("\nIf that's you, save it (then reopen PowerShell):")
print(f'  setx TELEGRAM_CHAT_ID "{next(iter(seen))}"')
