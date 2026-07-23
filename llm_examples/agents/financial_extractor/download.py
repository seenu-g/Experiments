"""
Step 1: download the latest annual report PDF for a symbol via NSE's
(unofficial) annual-reports API -- session-cookie trick, since a plain
request to the API 401/403s without first visiting the homepage. Works
uniformly across companies (unlike scraping each company's own
investor-relations site, which can be blocked by bot protection like
Akamai on some sites).
"""

from datetime import datetime
from pathlib import Path

import requests

from . import config


def _nse_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    s.get("https://www.nseindia.com", timeout=15)  # picks up session cookies
    return s


def latest_annual_report_url(symbol: str) -> str:
    session = _nse_session()
    response = session.get(
        f"https://www.nseindia.com/api/annual-reports?index=equities&symbol={symbol}",
        timeout=15,
    )
    response.raise_for_status()
    entries = [e for e in response.json()["data"] if e["fileName"].lower().endswith(".pdf")]
    if not entries:
        raise RuntimeError(f"no PDF annual reports found for {symbol} (only zips/other formats)")
    latest = max(
        entries,
        key=lambda e: datetime.strptime(e["disseminationDateTime"], "%d-%b-%Y %H:%M:%S"),
    )
    return latest["fileName"]


def download_report(symbol: str) -> Path:
    dest = config.CACHE_DIR / f"{symbol}.pdf"
    if dest.exists():
        print(f"  [cache hit] {dest}")
        return dest

    url = latest_annual_report_url(symbol)
    print(f"  downloading {url}")
    # Stream to disk in chunks instead of loading the whole ~10MB file into
    # memory at once (response.content) -- matters once this loops over 80
    # reports, especially if any run concurrently.
    with requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60, stream=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    return dest


if __name__ == "__main__":
    # python -m agents.financial_extractor.download WIPRO INFY TCS
    import sys

    symbols = sys.argv[1:] or ["WIPRO", "INFY"]
    for symbol in symbols:
        print(f"\n=== {symbol} ===")
        try:
            download_report(symbol)
        except Exception as e:
            print(f"  [failed] {symbol}: {e}")
