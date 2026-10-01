"""
store_tweets.py — Where collected tweets live on disk. The app owns this; no model involved.

    tweets/2026-W40/<tweet id>/tweet.json   <- the record: the source of truth
    tweets/2026-W40/<tweet id>/1.jpg ...    <- downloaded photos
    tweets/2026-W40/report.html             <- a view, rebuilt from the records (report.py)

Weeks are ISO weeks (Monday-Sunday), named by the day the tweet was read.
Later jobs (image text, category) fill in fields that start empty here: a record missing a
field is simply "not done yet", so jobs can be re-run safely.
"""

import json
import os
from datetime import datetime

TWEETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tweets")


def week_name(when: datetime) -> str:
    year, week, _ = when.isocalendar()
    return f"{year}-W{week:02d}"


def week_dir(week: str) -> str:
    return os.path.join(TWEETS_DIR, week)


def record_path(week: str, tweet_id: str) -> str:
    return os.path.join(week_dir(week), tweet_id, "tweet.json")


def exists(week: str, tweet_id: str) -> bool:
    return os.path.exists(record_path(week, tweet_id))


# Write to a temp file, then rename over the real one: a crash mid-write can never leave a
# half-written tweet.json that would break every later job and report.
def save(record: dict) -> str:
    path = record_path(record["week"], record["id"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


# All records of a week, oldest read first. An unreadable file is skipped with a note,
# so one bad record can't stop the report.
def load_week(week: str) -> list[dict]:
    folder = week_dir(week)
    if not os.path.isdir(folder):
        return []
    records = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name, "tweet.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                records.append(json.load(f))
        except (OSError, ValueError) as e:
            print(f"Skipping unreadable {path}: {e}")
    return sorted(records, key=lambda r: r.get("read_at", ""))
