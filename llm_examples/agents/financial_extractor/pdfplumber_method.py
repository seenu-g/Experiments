"""
Step 2: extract text page by page with pdfplumber, and score each page by
how many target-field keywords/section headers/currency figures it
contains. Keep only the highest-scoring pages -- this is the step that
makes a local model viable: a handful of relevant pages instead of 500.

Upgrade over the original flat-text-only approach: for the final selected
pages only (never all 500+, which would be too slow), also run
page.extract_tables() and append a simple pipe-row rendering of any tables
found. Flat text extraction flattens table rows/columns into ambiguous
prose (this caused a real bug: a net_profit value came back as a vague
"X to Y" range instead of one clean figure, because the source table's
column structure -- which year each number belonged to -- was lost).
Preserving row/column structure gives the LLM a much clearer signal.
"""

import pdfplumber

from . import config


def _render_tables(page) -> str:
    """Render any tables on this page as simple pipe-separated rows, so
    column/row structure survives instead of being flattened into prose.
    Returns "" if the page has no detected tables.

    Skips tables where every row has at most one non-empty cell -- on pages
    with two side-by-side tables (seen on WIPRO's financial-highlights page),
    pdfplumber's table detector sometimes collapses each sub-table into a
    single column of bare numbers with the row labels stripped entirely. That
    kind of "table" carries no more information than the flat extract_text()
    already provides and is worse (no labels), so it's pure noise appended to
    the LLM prompt rather than a useful structure signal -- better to omit it
    and let the flat text (which still has "Share Capital  20,977 ...") do
    the job."""
    tables = page.extract_tables()
    if not tables:
        return ""
    rendered = []
    for table in tables:
        non_empty_counts = [sum(1 for c in row if c is not None and str(c).strip()) for row in table]
        if non_empty_counts and max(non_empty_counts) <= 1:
            continue
        for row in table:
            cells = [str(c).strip() if c is not None else "" for c in row]
            rendered.append(" | ".join(cells))
    return "\n".join(rendered)


def extract_relevant_pages(pdf_path, top_n: int = 6) -> tuple[list[dict], int]:
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
            score = len(config.KEYWORD_PATTERN.findall(lower))
            # Capped at 1: a running page header (e.g. "Standalone Financial
            # Statement" repeated on every page of a ~100-page section) would
            # otherwise inflate a boilerplate/prose page's score far above an
            # actual numbers table just by repetition.
            score += config.SECTION_HEADER_WEIGHT * min(len(config.SECTION_HEADER_PATTERN.findall(lower)), 1)
            score -= config.NEGATIVE_SECTION_HEADER_WEIGHT * len(config.NEGATIVE_SECTION_HEADER_PATTERN.findall(lower))
            # The actual signal that matters most: does this page contain
            # real currency-formatted figures? A genuine data table will have
            # several; a page that merely discusses/mentions the keywords in
            # prose won't. Without this, a keyword-dense narrative page can
            # outscore the real numbers table.
            score += config.CURRENCY_HIT_WEIGHT * len(config.CURRENCY_RE.findall(text))
            score = max(score, 0)
            if score:
                scored_pages.append((score, i, text))
            # pdfplumber caches each page's parsed layout objects (chars,
            # rects, etc.) internally, and pdf.pages holds every Page for the
            # life of this `with` block -- without flushing, that cache grows
            # across all 500+ pages even though we only keep 6 text strings.
            page.flush_cache()

    scored_pages.sort(key=lambda t: t[0], reverse=True)
    top = scored_pages[:top_n]

    # Coverage top-up: a field like share_capital lives almost exclusively on
    # the Balance Sheet page, which has ~30 mostly-irrelevant line items and
    # only ONE mention of "share capital" -- it will never win a
    # keyword-density contest against a "financial highlights" page that
    # packs every metric into one table, no matter how the scoring weights
    # above are tuned (tried that, it just displaces other good pages
    # instead -- see git history). So rather than one ranking formula
    # serving every field, check which fields have no keyword hit anywhere
    # in `top`, and for each, pull in the single best-scoring page (from the
    # full scan, even if its overall score didn't make top_n) that does
    # contain that field's keyword. Capped so one report with several
    # genuinely-absent fields can't balloon the page set/LLM prompt.
    MAX_COVERAGE_TOPUPS = 3
    top_indices = {i for _, i, _ in top}
    covered_text = "\n".join(text.lower() for _, _, text in top)
    missing_fields = [
        field for field, pattern in config.FIELD_KEYWORD_PATTERNS.items()
        if not pattern.search(covered_text)
    ]
    added = 0
    for field in missing_fields:
        if added >= MAX_COVERAGE_TOPUPS:
            break
        pattern = config.FIELD_KEYWORD_PATTERNS[field]
        candidate = next(
            (t for t in scored_pages if t[1] not in top_indices and pattern.search(t[2].lower())),
            None,
        )
        if candidate:
            top.append(candidate)
            top_indices.add(candidate[1])
            added += 1
    if added:
        print(f"  coverage top-up: added {added} page(s) for field(s) with no keyword hit in the top {top_n}")

    top = sorted(top, key=lambda t: t[1])  # restore reading order
    print(f"  kept {len(top)} of {len(scored_pages)} keyword-matching pages "
          f"(page numbers: {[i + 1 for _, i, _ in top]})")

    # Second, targeted pass: run extract_tables() only on the handful of
    # pages we actually kept (extract_tables() is much slower than
    # extract_text(), so it isn't run across all 500+ pages in the scoring
    # pass above).
    top_indices = {i for _, i, _ in top}
    tables_by_index = {}
    if top_indices:
        with pdfplumber.open(pdf_path) as pdf:
            for i in top_indices:
                table_text = _render_tables(pdf.pages[i])
                if table_text:
                    tables_by_index[i] = table_text
                pdf.pages[i].flush_cache()

    pages = []
    for score, i, text in top:
        table_text = tables_by_index.get(i, "")
        combined_text = f"{text}\n\n--- TABLES ON THIS PAGE ---\n{table_text}" if table_text else text
        unit_match = config.UNIT_CAPTION_RE.search(text)
        if unit_match:
            currency, magnitude = unit_match.groups()
            currency = "₹" if currency.lower() in ("rs", "rs.", "inr") else currency
            note = f"[UNIT NOTE: bare figures on this page are stated in {currency} {magnitude.lower()} unless the figure itself gives a different unit]"
            combined_text = f"{note}\n\n{combined_text}"
        pages.append({"page_number": i + 1, "score": score, "text": combined_text})
    return pages, total_pages


def combine_page_texts(pages: list[dict]) -> str:
    return "\n\n".join(p["text"] for p in pages)
