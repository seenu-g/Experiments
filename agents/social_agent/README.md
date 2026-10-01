# Social Agent — Personal Tweet Collector

Collects tweets I want to keep, saves them per week as JSON, and builds an HTML report
to read them. Tweets come from the command line, a text file of links, or from sharing
them to my own Telegram bot from my phone. Runs fully locally: Python + Ollama, no paid APIs.

## How it works

```
tweet links ──► collect_tweets.py ──► tweets/<week>/<id>/tweet.json + photos ──► report.html
  (args, a .txt file,                  (the record = source of truth)            (a view, rebuilt
   or telegram_inbox.py)                                                          from the records)

later jobs read the records and fill in empty fields:
  extract_text_from_images.py ──► image_text      (planned: vision model)
  classify_tweet.py           ──► category        (planned: small text model)
```

Design choices:
- **JSON first, HTML second.** `tweet.json` is the record; `report.html` is generated from
  it and can be rebuilt any time (new design, new categories) without fetching anything again.
- **Collecting is fast; slow model work runs separately.** A record missing a field is
  simply "not done yet", so jobs can be stopped and re-run safely and never redo work.
- **The app owns state, the model only does language.** Week folders, duplicates, who may
  send links, and allowed categories are decided in code; models only read images and
  (later) pick a category from a fixed list.

## Setup

```powershell
pip install requests ollama pillow
ollama pull qwen2.5vl:3b        # vision model, only needed for reading images
```

Tweets are fetched through [fxtwitter](https://github.com/FixTweet/FxTwitter), an unofficial
free API — no X account or key needed, but it can change or be unavailable.

## Usage

```powershell
python collect_tweets.py <tweet url> [<tweet url> ...]   # collect into this week's folder
python collect_tweets.py urls.txt                        # links anywhere in a text file
python report.py                                         # rebuild this week's report
python report.py 2026-W40                                # rebuild a given week
python telegram_inbox.py                                 # collect links shared to the bot
python telegram_inbox.py --loop                          # keep running, pick up shares in seconds
python read_tweet.py <tweet url>                         # standalone: print one tweet + image text
```

In a links file, tweet URLs are picked out of any text; other text, blank lines and lines
starting with `#` are ignored, and repeated links are read once. A tweet already collected
this week is skipped.

Open `tweets\<week>\report.html` in a browser to read the week.

## Folder layout

```
social_agent/
  tweets/2026-W40/                 ISO week (Monday–Sunday) of the day a tweet was collected
    report.html
    2105364594902327795/
      tweet.json
      1.jpg, 2.png ...             full-size photos
```

`tweet.json` fields:

| Field | Meaning |
|---|---|
| `id`, `url`, `author`, `text` | The tweet (`url` without tracking parameters) |
| `photos` | Original photo URLs |
| `images` | Downloaded file names, e.g. `["1.jpg"]` |
| `read_at`, `week` | When it was collected, and its week folder |
| `image_text` | One entry per image — `null` until the image job runs |
| `image_error` | Why images could not be read, if they failed |
| `category` | `null` until the classify job runs |
| `photo_error` | Present only if a photo download failed (the tweet is still kept) |

## Telegram inbox (share tweets from your phone)

1. In Telegram, open **@BotFather** (blue checkmark) → `/newbot` → choose a name and a
   username ending in `bot` → copy the **token**. Optionally `/setjoingroups` → Disable.
2. Open your bot, press **Start**, send it `hello`.
3. Put the token where the scripts can read it (pick one):
   - `telegram_config.json` next to the scripts: `{"bot_token": "123:ABC...", "chat_id": 123456789}`
   - or environment variables: `setx TELEGRAM_BOT_TOKEN "..."` and `setx TELEGRAM_CHAT_ID "..."`,
     then reopen the terminal (in VS Code: restart VS Code itself).
4. Find your chat id: `python show_chat_id.py` — it prints the id and the `setx` line to use.
5. Share tweets to the bot (X app → Share → Telegram → your bot, or paste links), then run
   `python telegram_inbox.py`. The bot replies with a summary, e.g. `Tweets: saved 2, skipped 1.`

Only messages from your chat id are used; anything else is ignored. Handled messages are
remembered in `telegram_state.json`, so nothing is processed twice. **Telegram keeps
undelivered messages for about 24 hours** — run the inbox at least once a day.

Run it automatically every 30 minutes (Windows Task Scheduler, runs while you are logged in):

```powershell
$py = (Get-Command python).Source
schtasks /Create /SC MINUTE /MO 30 /TN "TweetInbox" /TR "cmd /c `"`"$py`" `"D:\code\Experiments\agents\social_agent\telegram_inbox.py`" >> `"D:\code\Experiments\agents\social_agent\inbox_log.txt`" 2>&1`""
schtasks /Delete /TN "TweetInbox" /F      # to remove it
```

## Reading text in images (vision model)

`read_tweet.py` holds the vision settings, at the top:

| Setting | Default | Notes |
|---|---|---|
| `VISION_MODEL` | `qwen2.5vl:3b` | Must be pulled. On a CPU-only 16 GB laptop the whole model must fit in **free** RAM, or it swaps and times out. `qwen2.5vl:3b` (~3 GB) < `qwen2.5vl:7b` (~6 GB) < `gemma4:e4b` (~10 GB) |
| `VISION_MAX_SIDE` | `1024` | Images are shrunk before sending (the original stays on disk). A 3072px photo is ~11,600 image tokens; 1024px is ~1,300 |
| `VISION_CTX` | `4096` | Context reserved per call; one image + prompt needs < 2,000 tokens |
| `VISION_TIMEOUT` | `300` | Seconds per image; the first call also loads the model |

The image text is the **model's reading**, not exact text — it can misread words.

## Files

| File | Purpose |
|---|---|
| `collect_tweets.py` | Collect tweets (args or text file) into the week folder; rebuild the report |
| `store_tweets.py` | Week folders, safe saving of `tweet.json` (temp file + rename), loading a week |
| `report.py` | Build `report.html` from a week's records |
| `read_tweet.py` | Fetch a tweet (fxtwitter), download photos, read images with the vision model |
| `telegram_inbox.py` | Collect tweet links shared to your Telegram bot |
| `show_chat_id.py` | One-time helper to find your Telegram chat id |
| `.gitignore` | Keeps the token, state, logs and collected data out of git |

`telegram_config.json` (your token), `telegram_state.json`, `tweets/` and `images/` are
not in git. `tweets/` exists only on this machine — back it up if it matters.

## Troubleshooting

| Problem | Fix |
|---|---|
| `No bot token / chat id found` | Create `telegram_config.json`, or reopen the terminal after `setx` (restart VS Code if using its terminal) |
| Image reading `timed out` | Usually out of free RAM: use `qwen2.5vl:3b`, close other apps, check `ollama ps`; or lower `VISION_MAX_SIDE` |
| `Could not read tweet …` | Deleted or private tweet, or fxtwitter temporarily unavailable — try again later |
| Many PowerShell errors after pasting code | Python code was pasted into PowerShell; run the `.py` file with `python` instead |

## Roadmap

1. ~~Collect tweets per week, JSON records, HTML report~~ ✓
2. ~~Text-file input and Telegram inbox~~ ✓
3. `extract_text_from_images.py` — fill `image_text` for records that don't have it yet
4. `classify_tweet.py` — pick a category (e.g. AI, Spiritual, Tech) from a fixed list, with
   `Other` as default; the model's answer is constrained to the list and checked in code
5. Category views in the report (sections or one page per category)
