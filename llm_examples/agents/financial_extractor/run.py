"""
Step 5: the actual function that pulls everything together for one stock
symbol -- download, extract (via either the pdfplumber or markdown
strategy), LLM extraction, validation, and audit logging.

Run with: python -m agents.financial_extractor.run
"""

import pdfplumber

from . import config, download, llm_extract, markdown_method, pdfplumber_method, validate


def run(symbol: str, method: str = "pdfplumber", model: str = config.DEFAULT_MODEL) -> dict:
    """Returns {"fields", "warnings", "sources", "pages", "total_pages",
    "log_path"} -- not just the extracted fields -- so callers like eval.py
    can report which page(s) each value was traced back to and which
    validation warnings fired, without re-running the pipeline themselves."""
    if method not in ("pdfplumber", "markdown"):
        raise ValueError(f"unknown method {method!r}, expected 'pdfplumber' or 'markdown'")

    print(f"\n=== {symbol} (method={method}) ===")
    pdf_path = download.download_report(symbol)

    if method == "pdfplumber":
        pages, total_pages = pdfplumber_method.extract_relevant_pages(pdf_path)
        text = pdfplumber_method.combine_page_texts(pages)
        print(f"  extracted {len(text)} chars from {len(pages)} pages (vs. full {total_pages}-page doc)")
    else:
        # markdown_method converts the whole document -- no per-page
        # selection yet, so `pages` stays empty (see validate.py notes on
        # attribute_source_pages / write_audit_log).
        text = markdown_method.convert_to_markdown(pdf_path, symbol)
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
        pages = []
        print(f"  extracted {len(text)} chars from markdown conversion of the full {total_pages}-page doc")

    fields = llm_extract.extract_fields_with_llm(text, model=model)
    print(f"  result: {fields}")

    warnings = validate.validate_fields(fields)
    if warnings:
        print("  validation warnings:")
        for field, msg in warnings.items():
            print(f"    [{field}] {msg}")

    if method == "pdfplumber":
        sources = validate.attribute_source_pages(fields, pages)
        print("  field sources (page numbers each value was traced back to):")
        for field, value in fields.items():
            if value is not None:
                print(f"    [{field}] = {value!r} -> page(s) {sources.get(field, 'not found on any selected page')}")
    else:
        sources = {}
        print("  field sources: skipped (markdown method has no per-page breakdown to attribute against)")

    log_path = validate.write_audit_log(symbol, pdf_path, total_pages, pages, fields, sources, warnings, method)
    print(f"  audit log written to: {log_path}")

    return {
        "fields": fields,
        "warnings": warnings,
        "sources": sources,
        "pages": pages,
        "total_pages": total_pages,
        "log_path": log_path,
    }


if __name__ == "__main__":
    for symbol in ["WIPRO", "INFY"]:
        run(symbol, method="pdfplumber")
