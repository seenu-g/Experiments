"""
report.py — Build tweets/<week>/report.html from that week's tweet.json records.

The HTML is only a view: rebuild any week at any time without fetching or re-reading anything.
    python report.py              # current week
    python report.py 2026-W40     # a given week

Per tweet: URL, author and text, then the images, each followed by its image text
(or "not read yet" until the image job has run). Image paths are relative, so a week
folder still works when copied or zipped.
"""

import html
import os
import sys
from datetime import datetime

import store_tweets

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tweets {week}</title>
<style>
  :root {{ --bg: #fafaf8; --card: #fff; --text: #222; --muted: #6b6b6b; --line: #e4e4e0; --accent: #2f6fb3; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #17181a; --card: #202225; --text: #e6e6e3; --muted: #9a9a96; --line: #34363a; --accent: #7fb0e6; }}
  }}
  body {{ background: var(--bg); color: var(--text); font: 16px/1.55 system-ui, sans-serif;
          max-width: 760px; margin: 0 auto; padding: 24px 16px; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .meta, .muted {{ color: var(--muted); font-size: .9rem; }}
  article {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
             padding: 16px; margin: 18px 0; }}
  a {{ color: var(--accent); word-break: break-all; }}
  .text {{ white-space: pre-wrap; margin: 10px 0; }}
  figure {{ margin: 14px 0 0; }}
  img {{ max-width: 100%; border-radius: 8px; border: 1px solid var(--line); }}
  figcaption {{ white-space: pre-wrap; font-size: .92rem; margin-top: 6px; }}
  .tag {{ display: inline-block; font-size: .8rem; padding: 1px 8px; border-radius: 99px;
          border: 1px solid var(--line); color: var(--muted); }}
</style></head><body>
<h1>Tweets — week {week}</h1>
<p class="meta">{count} tweet(s) · generated {generated}</p>
{articles}
</body></html>
"""


def _caption(record: dict, i: int) -> str:
    texts = record.get("image_text")              # filled later by the image job
    if texts and i < len(texts) and texts[i]:
        return f"<figcaption><span class='muted'>Image text (model's reading):</span>\n{html.escape(texts[i])}</figcaption>"
    if record.get("image_error"):
        return f"<figcaption class='muted'>Image not read: {html.escape(record['image_error'])}</figcaption>"
    return "<figcaption class='muted'>Image text: not read yet</figcaption>"


def _article(record: dict) -> str:
    esc = html.escape
    category = f" <span class='tag'>{esc(record['category'])}</span>" if record.get("category") else ""
    parts = [
        f"<article><a href='{esc(record['url'])}'>{esc(record['url'])}</a>{category}",
        f"<div class='meta'>{esc(record['author'])} · read {esc(record['read_at'][:16].replace('T', ' '))}</div>",
        f"<div class='text'>{esc(record['text'])}</div>",
    ]
    for i, image in enumerate(record.get("images", [])):
        src = f"{record['id']}/{image}"           # relative to report.html
        parts.append(f"<figure><img src='{esc(src)}' alt='Image {i + 1}' loading='lazy'>{_caption(record, i)}</figure>")
    if record.get("photo_error"):
        parts.append(f"<p class='muted'>Some photos could not be downloaded: {esc(record['photo_error'])}</p>")
    parts.append("</article>")
    return "\n".join(parts)


def build_report(week: str) -> str | None:
    records = store_tweets.load_week(week)
    if not records:
        return None
    page = PAGE.format(week=html.escape(week), count=len(records),
                       generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
                       articles="\n".join(_article(r) for r in records))
    path = os.path.join(store_tweets.week_dir(week), "report.html")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(page)
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    week = sys.argv[1] if len(sys.argv) > 1 else store_tweets.week_name(datetime.now())
    path = build_report(week)
    print(f"Report: {path}" if path else f"No tweets stored for week {week}")
