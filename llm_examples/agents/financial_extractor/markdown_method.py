"""
Step 3: convert the whole PDF to markdown using markitdown, as an
alternative to pdfplumber_method's page-scoring approach. Markdown
conversion generally preserves table/heading structure better than flat
text extraction, which is the source of at least one real bug seen with
the pdfplumber path (a table's column structure getting lost, producing an
ambiguous range instead of a clean figure).

Unlike pdfplumber_method, this converts the ENTIRE document, not a
pre-selected handful of pages -- the point right now is to inspect markdown
quality across the whole report before deciding whether/how to restrict it
to specific pages the way the pdfplumber method does. Slower per report
(full document conversion) but useful for a side-by-side quality check
against the source PDF.
"""

from pathlib import Path

from markitdown import MarkItDown

from . import config


def convert_to_markdown(pdf_path: Path, symbol: str, save: bool = True) -> str:
    """Convert the full PDF to markdown. If save=True (default), also write
    it to report_cache/{symbol}.md next to the cached PDF, so it can be
    opened side by side with the source PDF for a manual quality check."""
    print(f"  converting {pdf_path} to markdown (full document)...")
    result = MarkItDown().convert(pdf_path)
    text = result.text_content

    if save:
        md_path = config.CACHE_DIR / f"{symbol}.md"
        md_path.write_text(text, encoding="utf-8")
        print(f"  saved markdown to {md_path} (open next to {pdf_path} to compare)")

    return text
