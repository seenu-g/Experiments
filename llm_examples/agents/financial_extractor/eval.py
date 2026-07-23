"""
Eval harness: run the pdfplumber extraction pipeline against known-good
figures for WIPRO and INFY (values manually verified against the source PDF
in report_cache/ -- see the page-38 dump from 2026-07-23), and check that:
  - the expected figure is still present in each field's value
  - currency fields (share_capital/sales/revenue/gross_profit/net_profit)
    carry a unit and don't trip validate.py's CURRENCY_RE warning

This is what caught (and now guards against regressing) the WIPRO bug where
a page states its unit once as a caption -- "(Figures in Rs million except
otherwise stated)" -- instead of inline per figure, so bare numbers came
back with no currency unit attached.

Not a full regression suite (no ground truth for every field on every
company, and no `sales`/`dividend`/`gross_profit` values on pages where the
report genuinely doesn't state them) -- just enough to catch this pipeline
regressing on the two reports already in report_cache/.

Results are written to a markdown report instead of only being printed --
with more than a couple of symbols, scrolling back through terminal output
to compare a field's old vs. new value (and which page it came from) stops
being practical. Each run is saved as its own timestamped file (so two runs
can be diffed directly to check whether a fix actually improved something)
plus eval_results/latest.md, which always holds the most recent run's
report under a fixed name.

Run with: python -m agents.financial_extractor.eval
"""

from datetime import datetime

from . import config, run, validate

# Manually verified against report_cache/{symbol}.pdf. WIPRO states its unit
# once as a page caption ("Rs million"); INFY states it inline per figure
# ("Rs 1,23,531 crore") -- exercises both cases.
EXPECTED = {
    "WIPRO": {
        "share_capital": "20,977",
        "revenue": "928,093",
        "gross_profit": "271,901",
        "net_profit": "131,974",
        "eps_basic": "12.60",
        "eps_diluted": "12.56",
    },
    "INFY": {
        "share_capital": "2,027",
        "sales": "1,01,584",
        "revenue": "1,23,531",
        "net_profit": "29,440",
        "eps_basic": "71.58",
        "eps_diluted": "71.58",
    },
}

CURRENCY_FIELDS = {"share_capital", "sales", "revenue", "gross_profit", "net_profit"}

RESULTS_DIR = config.AUDIT_LOG_DIR.parent / "eval_results"


# Compares `result` (as returned by run.run) against EXPECTED[symbol].
# Returns {field: status} for every field in result["fields"], where status
# is "PASS", "FAIL: <reason>", or "n/a" (no ground truth for this field).
def check_symbol(symbol: str, result: dict) -> dict:
    fields = result["fields"]
    warnings = result["warnings"]
    expected = EXPECTED.get(symbol, {})

    statuses = {}
    for field, value in fields.items():
        if field not in expected:
            statuses[field] = "n/a"
            continue
        if value is None:
            statuses[field] = f"FAIL: expected value containing {expected[field]!r}, got None"
            continue
        if expected[field] not in str(value):
            statuses[field] = f"FAIL: expected value containing {expected[field]!r}, got {value!r}"
            continue
        if field in CURRENCY_FIELDS and field in warnings:
            statuses[field] = f"FAIL: {warnings[field]}"
            continue
        statuses[field] = "PASS"
    return statuses


# run_results: {symbol: result-dict-from-run.run}. all_statuses:
# {symbol: {field: status}} as returned by check_symbol. Returns a markdown
# report: one table per symbol with each field's value, source page(s), and
# pass/fail status, plus an overall summary table up top.
def render_report(run_results: dict, all_statuses: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Financial extractor eval -- {timestamp}", ""]

    lines.append("| Symbol | Result |")
    lines.append("|---|---|")
    for symbol, statuses in all_statuses.items():
        fail_count = sum(1 for s in statuses.values() if s.startswith("FAIL"))
        verdict = "PASS" if fail_count == 0 else f"FAIL ({fail_count})"
        lines.append(f"| {symbol} | {verdict} |")
    lines.append("")

    for symbol, result in run_results.items():
        fields = result["fields"]
        sources = result["sources"]
        statuses = all_statuses[symbol]

        lines.append(f"## {symbol}")
        lines.append("")
        lines.append(f"log: `{result['log_path']}`")
        lines.append("")
        lines.append("| Field | Value | Page(s) | Status |")
        lines.append("|---|---|---|---|")
        for field, value in fields.items():
            page_refs = sources.get(field)
            page_str = ", ".join(str(p) for p in page_refs) if page_refs else "-"
            lines.append(f"| {field} | {value!r} | {page_str} | {statuses[field]} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    run_results = {}
    all_statuses = {}
    for symbol in EXPECTED:
        print(f"\n=== evaluating {symbol} ===")
        run_results[symbol] = run.run(symbol, method="pdfplumber")
        all_statuses[symbol] = check_symbol(symbol, run_results[symbol])

    report = render_report(run_results, all_statuses)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    dated_path = RESULTS_DIR / f"eval_{timestamp}.md"
    latest_path = RESULTS_DIR / "latest.md"
    dated_path.write_text(report, encoding="utf-8")
    latest_path.write_text(report, encoding="utf-8")

    any_fail = any(
        status.startswith("FAIL") for statuses in all_statuses.values() for status in statuses.values()
    )
    print(f"\nreport written to: {dated_path}")
    print(f"latest report always at: {latest_path}")
    print("result: " + ("FAIL" if any_fail else "PASS"))

    if any_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
