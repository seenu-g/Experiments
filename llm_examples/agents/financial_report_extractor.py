"""
Demo: pull specific financial fields out of a 500-page annual report PDF
using ONLY a local Ollama model, without stuffing the whole document into
context.

Pipeline:
1. Download the latest annual report PDF for a symbol via NSE's (unofficial)
   annual-reports API -- session-cookie trick, same one used to confirm
   NSE works uniformly across companies (unlike scraping each company's own
   investor-relations site).
2. Extract text page by page with pdfplumber, and score each page by how
   many target-field keywords it contains (share capital, sales, revenue,
   gross profit, net profit, dividend, EPS). Keep only the highest-scoring
   pages -- this is the step that makes a local model viable: a handful of
   relevant pages instead of 500.
3. Feed just those pages to a local model with a prompt asking for a fixed
   JSON schema, so the response is easy to parse and to sanity-check.

Run with: python financial_report_extractor.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import ollama
import pdfplumber
import requests

# Rupee amounts (₹) are core output here, but Windows consoles default to a
# codepage (cp1252) that can't encode ₹, crashing any print() that includes
# it. Force stdout/stderr to UTF-8 so this works regardless of the console's
# codepage, instead of erroring every time real figures are printed.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CACHE_DIR = Path(__file__).parent / "report_cache"
CACHE_DIR.mkdir(exist_ok=True)

MODEL = "llama3.1:latest"

FIELD_KEYWORDS = [
    "share capital",
    "authorized share capital",
    "authorised share capital",
    "sales",
    "revenue",
    "revenue from operations",
    "total revenue",
    "gross profit",
    "profit before tax",
    "net profit",
    "profit for the year",
    "profit after tax",
    "dividend per share",
    "dividend",
    "earnings per equity share",
    "earnings per share",
    "basic eps",
    "diluted eps",
    "basic and diluted",
    "eps",
]

# A stronger signal than any single keyword above: this exact section heading
# means the page is very likely to contain most/all target fields together.
SECTION_HEADERS = [
    "financial position",
    "financial performance",
    "standalone financial statement",
    "consolidated statement of profit and loss",
    "consolidated balance sheet",
]
SECTION_HEADER_WEIGHT = 10

# These section headers mean the page is very unlikely to hold the actual
# figures even if a target keyword happens to appear there in passing (e.g.
# "share capital" showing up inside an AGM resolution notice rather than an
# actual financial statement). Penalize hard enough to override keyword hits.
NEGATIVE_SECTION_HEADERS = [
    "annual general meeting",
    "notice to members",
    "notice",
    "board of directors",
    "executive committee",
    "leadership team",
    "business responsibility and sustainability report",
    "ceo and cfo certification",
    "social and relationship capital",
    "awards and recognitions",
    "statutory reports",
    "investor contacts",
    "investor contact",
]
NEGATIVE_SECTION_HEADER_WEIGHT = 15

# Several FIELD_KEYWORDS are substrings of others (e.g. "revenue" inside
# "revenue from operations", "share capital" inside "authorized share
# capital") -- naive substring counting would count one match twice. Building
# a single alternation regex (longest phrase first) makes matches
# non-overlapping: once "revenue from operations" matches, that span is
# consumed and "revenue" won't also match inside it.
_KEYWORD_PATTERN = re.compile(
    "|".join(re.escape(k) for k in sorted(FIELD_KEYWORDS, key=len, reverse=True))
)
_SECTION_HEADER_PATTERN = re.compile(
    "|".join(re.escape(h) for h in sorted(SECTION_HEADERS, key=len, reverse=True))
)
_NEGATIVE_SECTION_HEADER_PATTERN = re.compile(
    "|".join(re.escape(h) for h in sorted(NEGATIVE_SECTION_HEADERS, key=len, reverse=True))
)

FIELDS_SCHEMA = {
    "share_capital": "string in INR, e.g. 'Rs. 1,234 crore' or null if not found",
    "sales": "string in INR, or null",
    "revenue": "string in INR, or null",
    "gross_profit": "string in INR, or null",
    "net_profit": "string in INR, or null",
    "dividend": "string, per-share dividend or total, or null",
    "eps_basic": "string, Basic Earnings Per Equity Share, or null",
    "eps_diluted": "string, Diluted Earnings Per Equity Share, or null",
}

_CURRENCY_RE = re.compile(r"(rs\.?|inr|[₹?])\s*[\d,]+(\.\d+)?\s*(crore|lakh|million|billion)?", re.IGNORECASE)
# Weight per real currency-figure match found on a page -- the strongest
# signal that a page is an actual numbers table, not just prose that
# mentions the right words. See extract_relevant_pages.
CURRENCY_HIT_WEIGHT = 2
_PERCENT_RE = re.compile(r"[\d,]+(\.\d+)?\s*%")
# Not anchored: a decimal number can be present anywhere in a longer string
# like "Rs. 8.60 per equity share of Re. 1/- each" -- the field doesn't need
# to be *only* a number, just contain one.
_DECIMAL_RE = re.compile(r"[\d,]+\.\d+")
# Dividends are frequently stated as a bare number ("48.00 per share") with no
# currency symbol at all -- unlike share_capital/sales/etc., which are always
# large enough to come with an explicit currency/unit label in practice.
_PLAIN_NUMBER_RE = re.compile(r"[\d,]+(\.\d+)?\s*(per share)?", re.IGNORECASE)

# Each field's value must match at least one "any" pattern, and none of its
# "none" (reject) patterns. eps is the one that caught a real bug: the LLM
# returned "11.0 %" -- it contains a decimal, but a "%" means it's actually a
# percentage/growth figure, not an EPS value, so "%" is an explicit reject.
FIELD_VALUE_CHECKS = {
    "share_capital": {"any": [_CURRENCY_RE]},
    "sales": {"any": [_CURRENCY_RE]},
    "revenue": {"any": [_CURRENCY_RE]},
    "gross_profit": {"any": [_CURRENCY_RE]},
    "net_profit": {"any": [_CURRENCY_RE]},
    "dividend": {"any": [_CURRENCY_RE, _PERCENT_RE, _PLAIN_NUMBER_RE]},
    "eps_basic": {"any": [_DECIMAL_RE], "none": [_PERCENT_RE]},
    "eps_diluted": {"any": [_DECIMAL_RE], "none": [_PERCENT_RE]},
}


def validate_fields(fields: dict) -> dict:
    """Flag values whose shape doesn't match what that field should look
    like -- e.g. a '%' value in eps, which is a decimal, not a percentage."""
    warnings = {}
    for field, checks in FIELD_VALUE_CHECKS.items():
        value = fields.get(field)
        if value is None:
            continue
        text = str(value)
        any_patterns = checks.get("any", [])
        none_patterns = checks.get("none", [])
        if any_patterns and not any(p.search(text) for p in any_patterns):
            warnings[field] = f"value {value!r} doesn't look like a valid {field} (no match for {[p.pattern for p in any_patterns]})"
        elif any(p.search(text) for p in none_patterns):
            warnings[field] = f"value {value!r} looks wrong for {field} (matched a reject pattern: {[p.pattern for p in none_patterns if p.search(text)]})"
    return warnings


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
    dest = CACHE_DIR / f"{symbol}.pdf"
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


def extract_relevant_pages(pdf_path: Path, top_n: int = 6) -> tuple[list[dict], int]:
    """Return (pages, total_pages) where pages is the top_n highest-scoring
    pages as [{"page_number": 1-indexed, "score": int, "text": str}, ...], in
    reading order. Returning structured per-page data (not just one
    concatenated string) is what makes it possible to later trace an
    extracted field back to the specific page(s) it came from."""
    scored_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  scanning {total_pages} pages for financial-highlights keywords...")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lower = text.lower()
            score = len(_KEYWORD_PATTERN.findall(lower))
            # Capped at 1: a running page header (e.g. "Standalone Financial
            # Statement" repeated on every page of a ~100-page section) would
            # otherwise inflate a boilerplate/prose page's score far above an
            # actual numbers table just by repetition.
            score += SECTION_HEADER_WEIGHT * min(len(_SECTION_HEADER_PATTERN.findall(lower)), 1)
            score -= NEGATIVE_SECTION_HEADER_WEIGHT * len(_NEGATIVE_SECTION_HEADER_PATTERN.findall(lower))
            # The actual signal that matters most: does this page contain
            # real currency-formatted figures? A genuine data table will have
            # several; a page that merely discusses/mentions the keywords in
            # prose won't. Without this, a keyword-dense narrative page can
            # outscore the real numbers table.
            score += CURRENCY_HIT_WEIGHT * len(_CURRENCY_RE.findall(text))
            score = max(score, 0)
            if score:
                scored_pages.append((score, i, text))
            # pdfplumber caches each page's parsed layout objects (chars,
            # rects, etc.) internally, and pdf.pages holds every Page for the
            # life of this `with` block -- without flushing, that cache grows
            # across all 500+ pages even though we only keep 6 text strings.
            page.flush_cache()

    scored_pages.sort(key=lambda t: t[0], reverse=True)
    top = sorted(scored_pages[:top_n], key=lambda t: t[1])  # restore reading order
    print(f"  kept {len(top)} of {len(scored_pages)} keyword-matching pages "
          f"(page numbers: {[i + 1 for _, i, _ in top]})")
    pages = [{"page_number": i + 1, "score": score, "text": text} for score, i, text in top]
    return pages, total_pages


def combine_page_texts(pages: list[dict]) -> str:
    return "\n\n".join(p["text"] for p in pages)


def attribute_source_pages(fields: dict, pages: list[dict]) -> dict:
    """For each non-null extracted field, find which selected page(s) its
    numeric value actually appears on -- this is the audit trail: given a
    final answer, which specific page(s) of the 500-page PDF is it from."""
    sources = {}
    for field, value in fields.items():
        if value is None:
            continue
        numbers = _DECIMAL_RE.findall(str(value)) or re.findall(r"[\d,]{2,}", str(value))
        if not numbers:
            continue
        matching_pages = [
            p["page_number"] for p in pages if any(num in p["text"] for num in numbers)
        ]
        if matching_pages:
            sources[field] = matching_pages
    return sources


def write_audit_log(symbol: str, pdf_path: Path, total_pages: int, pages: list[dict],
                     fields: dict, sources: dict, warnings: dict) -> Path:
    """Persist a full audit trail to disk: which pages were scanned/kept,
    what each kept page scored and (truncated) contained, the final
    extracted fields, which page each field's value was traced back to, and
    any validation warnings. Console output disappears after the run; this
    doesn't."""
    log_dir = Path(__file__).parent / "audit_logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    log_path = log_dir / f"{symbol}_{timestamp}.json"

    record = {
        "symbol": symbol,
        "timestamp": timestamp,
        "pdf_path": str(pdf_path),
        "total_pages_in_pdf": total_pages,
        # Only the handful of pages we actually kept (never all 500+), and
        # only a short identifying snippet per page -- enough for a human to
        # recognize which section it is and spot-check, not a full copy of
        # the page content.
        "pages_selected": [
            {"page_number": p["page_number"], "score": p["score"], "snippet": p["text"][:120].strip()}
            for p in pages
        ],
        "extracted_fields": fields,
        "field_source_pages": sources,
        "validation_warnings": warnings,
    }
    log_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return log_path


def extract_fields_with_llm(text: str) -> dict:
    prompt = (
        "Extract these financial fields from the annual report excerpt below. "
        "Return ONLY a JSON object with exactly these keys, no other text:\n"
        f"{json.dumps(FIELDS_SCHEMA, indent=2)}\n\n"
        "CRITICAL: only use a value if the exact figure is literally present "
        "in the excerpt text below. Do not use any outside knowledge you may "
        "have about this company's real-world financial results -- if a "
        "field's figure does not literally appear in the excerpt, you MUST "
        "return null for it, even if you believe you know the real number. "
        "A null is the correct, expected answer when the excerpt simply "
        "doesn't contain that figure; a null is preferred to a "
        "remembered/guessed number.\n\n"
        "If a field isn't present in the excerpt, use null. Use the most "
        "recent year's figures if multiple years are shown. Some figures "
        "appear in both INR and USD (e.g. for ADR holders) -- always report "
        "the INR (Rs./₹) value, never the USD equivalent. 'Earnings per "
        "equity share' is usually reported as two separate figures, Basic "
        "and Diluted -- put them in eps_basic and eps_diluted respectively, "
        "don't merge them into one value.\n\n"
        "--- EXCERPT ---\n"
        f"{text[:12000]}"  # keep the request bounded even if page selection over-collects
    )
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    content = response["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(match.group(0)) if match else {"error": "unparseable response", "raw": content}


def run(symbol: str) -> dict:
    print(f"\n=== {symbol} ===")
    pdf_path = download_report(symbol)
    pages, total_pages = extract_relevant_pages(pdf_path)
    text = combine_page_texts(pages)
    print(f"  extracted {len(text)} chars from {len(pages)} pages (vs. full {total_pages}-page doc)")

    fields = extract_fields_with_llm(text)
    print(f"  result: {json.dumps(fields, indent=2)}")

    warnings = validate_fields(fields)
    if warnings:
        print("  validation warnings:")
        for field, msg in warnings.items():
            print(f"    [{field}] {msg}")

    sources = attribute_source_pages(fields, pages)
    print("  field sources (page numbers each value was traced back to):")
    for field, value in fields.items():
        if value is not None:
            print(f"    [{field}] = {value!r} -> page(s) {sources.get(field, 'not found on any selected page')}")

    log_path = write_audit_log(symbol, pdf_path, total_pages, pages, fields, sources, warnings)
    print(f"  audit log written to: {log_path}")

    return fields


if __name__ == "__main__":
    for symbol in ["WIPRO", "INFY"]:
        run(symbol)
