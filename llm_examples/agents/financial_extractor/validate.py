"""
Post-extraction QA: flag values whose shape doesn't match what that field
should look like, trace each value back to its source page(s) (audit
trail), and persist a full audit record to disk.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from . import config


def validate_fields(fields: dict) -> dict:
    """Flag values whose shape doesn't match what that field should look
    like -- e.g. a '%' value in eps, which is a decimal, not a percentage."""
    warnings = {}
    for field, checks in config.FIELD_VALUE_CHECKS.items():
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


def attribute_source_pages(fields: dict, pages: list[dict]) -> dict:
    """For each non-null extracted field, find which selected page(s) its
    numeric value actually appears on -- this is the audit trail: given a
    final answer, which specific page(s) of the PDF is it from. Only
    meaningful when `pages` is a list of per-page {page_number, text} dicts
    (the pdfplumber_method output) -- the markdown_method path converts the
    whole document at once, so there's no per-page breakdown to attribute
    against yet."""
    sources = {}
    for field, value in fields.items():
        if value is None:
            continue
        numbers = config.DECIMAL_RE.findall(str(value)) or re.findall(r"[\d,]{2,}", str(value))
        if not numbers:
            continue
        matching_pages = [
            p["page_number"] for p in pages if any(num in p["text"] for num in numbers)
        ]
        if matching_pages:
            sources[field] = matching_pages
    return sources


def write_audit_log(symbol: str, pdf_path: Path, total_pages: int, pages: list[dict],
                     fields: dict, sources: dict, warnings: dict, method: str) -> Path:
    """Persist a full audit trail to disk: which pages were scanned/kept,
    what each kept page scored and (truncated) contained, the final
    extracted fields, which page each field's value was traced back to, and
    any validation warnings. Console output disappears after the run; this
    doesn't."""
    config.AUDIT_LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    log_path = config.AUDIT_LOG_DIR / f"{symbol}_{timestamp}.json"

    record = {
        "symbol": symbol,
        "timestamp": timestamp,
        "method": method,
        "pdf_path": str(pdf_path),
        "total_pages_in_pdf": total_pages,
        # Only the handful of pages we actually kept (never all 500+), and
        # only a short identifying snippet per page -- enough for a human to
        # recognize which section it is and spot-check, not a full copy of
        # the page content. Empty for the markdown method (whole-document,
        # no per-page selection).
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
