import io
import os
import sys
from urllib.parse import urlparse

import requests
import ollama
from PIL import Image

DEFAULT_URL = "https://x.com/tinybuddha/status/2105364594902327795?s=20"
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")   # next to this script
TIMEOUT = 10                                                                      # seconds per request

# Vision model that reads the photos. Switch here; it must be pulled (`ollama pull <name>`)
# and support images. On a CPU-only 16 GB laptop size matters most: the whole model must fit
# in FREE RAM or it swaps and crawls. qwen2.5vl:3b (~3 GB) < qwen2.5vl:7b (~6 GB) < gemma4:e4b (~10 GB).
VISION_MODEL = "qwen2.5vl:3b"
VISION_CTX = 4096        # context to reserve; one shrunk image + prompt is < 2,000 tokens.
                         # Ollama's default here was 16,384, which reserves memory for nothing.
VISION_TIMEOUT = 300     # seconds per image; generous because the first call also loads the model
# Longest side sent to the model. Vision models turn pixels into tokens (qwen2.5vl: one per 28x28
# tile), so a 3072x2964 original is ~11,600 tokens - minutes on a CPU. 1024px is ~1,300 tokens and
# keeps tweet text readable. The full-size original stays on disk; only the copy sent is smaller.
VISION_MAX_SIDE = 1024
vision = ollama.Client(timeout=VISION_TIMEOUT)


class TweetError(Exception):
    pass


# Read one tweet via fxtwitter and return {"id", "author", "text", "photos"}.
# Only reads - no files written, nothing printed - so any caller (main, or an agent tool later)
# can use it. Raises TweetError with a readable reason instead of exiting.
def read_tweet(url: str) -> dict:
    if "/status/" not in url:
        raise TweetError(f"Not a tweet URL: {url}")
    tweet_id = url.rstrip("/").split("/status/")[1].split("?")[0]

    try:
        resp = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", timeout=TIMEOUT)
        data = resp.json()
    except (requests.RequestException, ValueError) as e:  # no connection, timeout, or not JSON
        raise TweetError(f"Could not reach fxtwitter: {e}") from e

    # fxtwitter reports its own status in the JSON (code/message), e.g. 404 for a deleted tweet
    if data.get("code") != 200 or "tweet" not in data:
        raise TweetError(f"Could not read tweet {tweet_id}: {data.get('message', f'HTTP {resp.status_code}')}")

    tweet = data["tweet"]
    return {
        "id": tweet_id,
        "author": tweet["author"]["name"],
        "text": tweet["text"],
        "photos": [p["url"] for p in (tweet.get("media") or {}).get("photos", [])],
    }


# Save a tweet's photos to <folder>/<tweet id>/1.jpg, 2.png, ... and return the saved paths.
# The extension comes from the photo URL (X serves both jpg and png). A failed download raises
# TweetError, so an error page is never saved as an image.
def download_photos(tweet: dict, folder: str = IMAGES_DIR) -> list[str]:
    if not tweet["photos"]:
        return []
    target = os.path.join(folder, tweet["id"])
    os.makedirs(target, exist_ok=True)

    saved = []
    for i, photo_url in enumerate(tweet["photos"], start=1):
        try:
            resp = requests.get(photo_url, timeout=TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise TweetError(f"Could not download photo {i} of tweet {tweet['id']}: {e}") from e
        ext = os.path.splitext(urlparse(photo_url).path)[1] or ".jpg"
        path = os.path.join(target, f"{i}{ext}")
        with open(path, "wb") as f:
            f.write(resp.content)
        saved.append(path)
    return saved


# JPEG bytes of the image with its longest side at most VISION_MAX_SIDE (smaller images unchanged).
def _shrink(path: str) -> bytes:
    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((VISION_MAX_SIDE, VISION_MAX_SIDE))   # keeps the aspect ratio
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


# Ask the vision model for the text in an image (or a one-sentence description if there is none).
# The answer is the MODEL'S READING, not exact text - it can misread or invent words.
# Any failure (Ollama not running, model not pulled, timeout, unreadable file) raises TweetError.
def read_image(path: str, model: str = VISION_MODEL) -> str:
    try:
        response = vision.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": "Extract all text from this image exactly as written. "
                           "If there is no text, describe the image in one sentence.",
                "images": [_shrink(path)],
            }],
            options={"num_ctx": VISION_CTX},
        )
    except Exception as e:                       # ConnectionError, ollama.ResponseError, timeout, file errors
        raise TweetError(f"Could not read image {path} with {model}: {e}") from e
    return response["message"]["content"].strip()


# Usage: python read_tweet.py <tweet url> [<tweet url> ...]   (no url: DEFAULT_URL is read)
# Prints each tweet, saves its photos under images/<tweet id>/, and prints what the vision
# model reads in each photo. Exit code 0 if everything worked, 1 if anything failed.
def main(urls: list[str]) -> int:
    failed = 0
    for url in urls or [DEFAULT_URL]:
        try:
            tweet = read_tweet(url)
            print(tweet["author"], "-", tweet["text"])
            for path in download_photos(tweet):
                print("Saved", path)
                try:                             # one unreadable image must not skip the others
                    print(f"Image text ({VISION_MODEL}'s reading): {read_image(path)}")
                except TweetError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    failed += 1
        except TweetError as e:
            print(f"Error: {e}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
