"""
Shared constants and compiled regexes used by more than one module in this
package -- exists so pdfplumber_method.py and markdown_method.py don't
duplicate the keyword/schema/validation definitions.
"""

import re
import sys
from pathlib import Path

# Rupee amounts (₹) are core output here, but Windows consoles default to a
# codepage (cp1252) that can't encode ₹, crashing any print() that includes
# it. Force stdout/stderr to UTF-8 so this works regardless of the console's
# codepage, instead of erroring every time real figures are printed.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CACHE_DIR = Path(__file__).parent / "report_cache"
CACHE_DIR.mkdir(exist_ok=True)

AUDIT_LOG_DIR = Path(__file__).parent / "audit_logs"

DEFAULT_MODEL = "llama3.1:latest"

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
    # Plain/standalone balance sheet pages always carry an Equity Share
    # Capital line item -- previously only "consolidated balance sheet" was
    # listed, so a standalone balance sheet page only got this credit by
    # accident (e.g. an unrelated footer disclaimer happening to contain
    # "standalone financial statement"). Balance sheets can run 1-2 pages.
    "balance sheet",
]
SECTION_HEADER_WEIGHT = 10

# These section headers mean the page is very unlikely to hold the actual
# figures even if a target keyword happens to appear there in passing (e.g.
# "share capital" showing up inside an AGM resolution notice rather than an
# actual financial statement). Penalize hard enough to override keyword hits.
#
# NOTE: "board of directors" deliberately excluded -- a balance sheet's
# closing signature block ("for and on behalf of the Board of Directors of
# ...") contains that exact phrase, so it was firing on the very pages this
# scoring exists to find (e.g. INFY page 209), not on the bio/AGM pages it
# was meant to catch. "leadership team"/"executive committee" already cover
# those pages more precisely.
NEGATIVE_SECTION_HEADERS = [
    "annual general meeting",
    "notice to members",
    "notice",
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
KEYWORD_PATTERN = re.compile(
    "|".join(re.escape(k) for k in sorted(FIELD_KEYWORDS, key=len, reverse=True))
)
SECTION_HEADER_PATTERN = re.compile(
    "|".join(re.escape(h) for h in sorted(SECTION_HEADERS, key=len, reverse=True))
)
NEGATIVE_SECTION_HEADER_PATTERN = re.compile(
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

# Which FIELD_KEYWORDS entries actually indicate *this* field, as opposed to
# just contributing to a page's overall keyword-density score. Used for the
# coverage top-up in pdfplumber_method.extract_relevant_pages: a field like
# share_capital lives almost exclusively on the Balance Sheet page, which has
# ~30 mostly-irrelevant line items and only ONE mention of "share capital" --
# it will never win a density contest against a "financial highlights" page
# that packs every metric into one table, no matter how the scoring weights
# are tuned. So instead of trying to make one page-ranking formula serve
# every field, fields with no keyword hit among the top-scored pages get
# their own dedicated best-matching page pulled in as a supplement.
FIELD_KEYWORD_KEYWORDS = {
    "share_capital": ["share capital", "authorized share capital", "authorised share capital"],
    "sales": ["sales", "revenue from operations", "total revenue"],
    "revenue": ["revenue", "revenue from operations", "total revenue"],
    "gross_profit": ["gross profit"],
    "net_profit": ["profit before tax", "net profit", "profit for the year", "profit after tax"],
    "dividend": ["dividend per share", "dividend"],
    "eps_basic": ["basic eps", "earnings per equity share", "earnings per share", "eps"],
    "eps_diluted": ["diluted eps", "earnings per equity share", "earnings per share", "eps"],
}
FIELD_KEYWORD_PATTERNS = {
    field: re.compile("|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True)))
    for field, keywords in FIELD_KEYWORD_KEYWORDS.items()
}

CURRENCY_RE = re.compile(r"(rs\.?|inr|[₹?])\s*[\d,]+(\.\d+)?\s*(crore|lakh|million|billion)?", re.IGNORECASE)
# Some reports (e.g. WIPRO) state the unit once as a page-level caption --
# "(Figures in ₹ million except otherwise stated)" or "(₹ in million)" --
# and then every table row is a bare number with no unit attached. Detecting
# this caption lets pdfplumber_method prepend an explicit unit note to the
# page text, so the LLM has something to attach to those bare figures instead
# of emitting them unitless (which then fails CURRENCY_RE validation even
# though the figure itself is correct).
UNIT_CAPTION_RE = re.compile(
    r"\(?\s*(?:figures?\s+(?:are\s+)?)?(?:in\s+)?(rs\.?|inr|₹)\s*(?:in\s+)?(crore|lakh|million|billion)s?\b",
    re.IGNORECASE,
)
# Weight per real currency-figure match found on a page -- the strongest
# signal that a page is an actual numbers table, not just prose that
# mentions the right words. See pdfplumber_method.extract_relevant_pages.
CURRENCY_HIT_WEIGHT = 2
PERCENT_RE = re.compile(r"[\d,]+(\.\d+)?\s*%")
# Not anchored: a decimal number can be present anywhere in a longer string
# like "Rs. 8.60 per equity share of Re. 1/- each" -- the field doesn't need
# to be *only* a number, just contain one.
DECIMAL_RE = re.compile(r"[\d,]+\.\d+")
# Dividends are frequently stated as a bare number ("48.00 per share") with no
# currency symbol at all -- unlike share_capital/sales/etc., which are always
# large enough to come with an explicit currency/unit label in practice.
PLAIN_NUMBER_RE = re.compile(r"[\d,]+(\.\d+)?\s*(per share)?", re.IGNORECASE)

# Each field's value must match at least one "any" pattern, and none of its
# "none" (reject) patterns. eps is the one that caught a real bug: the LLM
# returned "11.0 %" -- it contains a decimal, but a "%" means it's actually a
# percentage/growth figure, not an EPS value, so "%" is an explicit reject.
FIELD_VALUE_CHECKS = {
    "share_capital": {"any": [CURRENCY_RE]},
    "sales": {"any": [CURRENCY_RE]},
    "revenue": {"any": [CURRENCY_RE]},
    "gross_profit": {"any": [CURRENCY_RE]},
    "net_profit": {"any": [CURRENCY_RE]},
    "dividend": {"any": [CURRENCY_RE, PERCENT_RE, PLAIN_NUMBER_RE]},
    "eps_basic": {"any": [DECIMAL_RE], "none": [PERCENT_RE]},
    "eps_diluted": {"any": [DECIMAL_RE], "none": [PERCENT_RE]},
}
