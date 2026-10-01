"""
collect_tweets.py — Read tweets into this week's folder and rebuild the week's report.

    python collect_tweets.py <tweet url> [<tweet url> ...]
    python collect_tweets.py urls.txt                    # a text file: tweet links anywhere in it
    python collect_tweets.py urls.txt <tweet url> ...    # files and URLs can be mixed

In a file, tweet links are picked out of any text (one per line or pasted with other text);
other text, blank lines and lines starting with # are ignored, and repeats are read once.

For each URL: fetch the tweet, download its photos, save tweet.json under
tweets/<week>/<tweet id>/, then rebuild tweets/<week>/report.html.
Fast on purpose - no model runs here. Image text and category start empty
and are filled later by separate jobs that read the saved records.
A tweet already collected this week is skipped.
"""

import os
import re
import sys
from datetime import datetime

import report
import store_tweets
from read_tweet import TweetError, download_photos, read_tweet


TWEET_URL = re.compile(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/\w+/status/\d+[^\s]*")


# Tweet links found anywhere in a piece of text (a file line, later a Telegram message).
def extract_urls(text: str) -> list[str]:
    return TWEET_URL.findall(text)


# Arguments -> URLs: a file argument is read for links, anything else is taken as a URL.
# Order is kept and repeats are dropped (the same tweet twice in one run is read once).
def gather_urls(args: list[str]) -> list[str]:
    urls = []
    for arg in args:
        if os.path.isfile(arg):
            with open(arg, encoding="utf-8") as f:
                for line in f:
                    if not line.lstrip().startswith("#"):
                        urls += extract_urls(line)
        else:
            urls.append(arg)
    seen, unique = set(), []
    for url in urls:
        key = url.split("?")[0]
        if key not in seen:
            seen.add(key)
            unique.append(url)
    return unique


# Fetch, download and save one tweet. Returns "saved", "skipped" or raises TweetError.
def collect(url: str, now: datetime) -> str:
    week = store_tweets.week_name(now)
    tweet = read_tweet(url)
    if store_tweets.exists(week, tweet["id"]):
        return "skipped"

    record = {
        "id": tweet["id"],
        "url": url.split("?")[0],                  # drop tracking parameters like ?s=20
        "author": tweet["author"],
        "text": tweet["text"],
        "photos": tweet["photos"],                 # original photo URLs
        "images": [],                              # downloaded file names, e.g. ["1.jpg"]
        "read_at": now.isoformat(timespec="seconds"),
        "week": week,
        "image_text": None,                        # filled by the image job (one entry per image)
        "image_error": None,
        "category": None,                          # filled by the classify job
    }
    try:
        paths = download_photos(tweet, folder=store_tweets.week_dir(week))
    except TweetError as e:                        # keep the tweet; note what is missing
        record["photo_error"] = str(e)
        folder = os.path.join(store_tweets.week_dir(week), tweet["id"])
        paths = [os.path.join(folder, n) for n in sorted(os.listdir(folder))] if os.path.isdir(folder) else []
    record["images"] = [os.path.basename(p) for p in paths if not p.endswith((".json", ".tmp"))]
    store_tweets.save(record)
    return "saved"


def main(args: list[str]) -> int:
    urls = gather_urls(args)
    if not urls:
        print(__doc__.strip() if not args else "No tweet URLs found.")
        return 1
    print(f"{len(urls)} tweet URL(s) to read")
    now = datetime.now()
    failed = 0
    for url in urls:
        try:
            print(f"{collect(url, now):8} {url}")
        except TweetError as e:
            print(f"Error: {e}", file=sys.stderr)
            failed += 1
    path = report.build_report(store_tweets.week_name(now))
    if path:
        print(f"Report: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
