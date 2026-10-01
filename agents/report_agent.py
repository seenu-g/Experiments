"""
Report agent: turns REQUIRE_REPORT (output of the 3 system tools) into an HTML report.

Code asks the user first (ask_save_location); the model runs only if the user says yes,
and only does the part that needs language: title, summary, file name.
It has no memory - each hand-off starts a brand-new conversation.
"""

import html
import os
import socket

from agent import Agent, StopAgent
from simple_agent import get_current_time
from system_agent import REQUIRE_REPORT, preview


def _render_html(title: str, summary: str, sections: dict[str, list[dict]]) -> str:
    esc = html.escape
    blocks = []
    for section, rows in sections.items():
        cols = list(rows[0]) if rows else []
        head = "".join(f"<th>{esc(c)}</th>" for c in cols)
        body = "".join(
            "<tr>" + "".join(f"<td>{esc(str(row.get(c, '')))}</td>" for c in cols) + "</tr>"
            for row in rows
        )
        blocks.append(
            f"<h2>{esc(section)} <small>({len(rows)})</small></h2>\n"
            f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; color: #222; }}
  h1 {{ margin-bottom: .2rem; }}  .meta {{ color: #777; margin-top: 0; }}
  .summary {{ background: #f4f6f8; border-left: 4px solid #4a78c2; padding: .8rem 1rem; }}
  h2 small {{ color: #777; font-weight: normal; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .9rem; margin-bottom: 2rem; }}
  th, td {{ text-align: left; padding: .35rem .6rem; border-bottom: 1px solid #e3e3e3; }}
  th {{ background: #fafafa; position: sticky; top: 0; }}
</style></head><body>
<h1>{esc(title)}</h1>
<p class="meta">Generated {esc(get_current_time())} on {esc(socket.gethostname())}</p>
<p class="summary">{esc(summary)}</p>
{chr(10).join(blocks)}
</body></html>
"""


# Where the user allowed the report to go - a folder or a file path. Set by ask_save_location()
# in code before the report agent runs; the model never sees or changes it.
_approved_location = ""


# Asked by the orchestrator BEFORE any model call: answering 'n' costs zero model calls.
def ask_save_location() -> bool:
    global _approved_location
    print(f"\n  [report] Create an HTML report of: {', '.join(REQUIRE_REPORT)}?")
    answer = input(f"  Enter/y = save in {os.getcwd()}, type a folder or file path, or 'n' to skip: ")
    answer = answer.strip().strip('"')
    if answer.lower() in {"n", "no"}:
        return False
    if answer.lower() in {"", "y", "yes"}:
        answer = os.getcwd()
    _approved_location = os.path.abspath(os.path.expanduser(answer))
    return True


def save_html_report(title: str, summary: str, filename: str) -> str:
    """Build an HTML report from the collected system data and save it.

    Args:
        title: Report title, e.g. 'System report for DESKTOP-01'
        summary: 2-4 sentence plain-text overview of the notable findings
        filename: Suggested file name ending in .html, e.g. 'services_report.html'
    """
    if not REQUIRE_REPORT or not _approved_location:
        raise StopAgent("Error: no system data or no approved save location.")
    name = os.path.basename(filename) or "system_report.html"
    if not name.lower().endswith(".html"):
        name += ".html"

    path = _approved_location                      # user gave a folder -> model's file name goes in it
    if os.path.isdir(path):
        path = os.path.join(path, name)
    elif not path.lower().endswith(".html"):       # "myreport" -> "myreport.html"
        path += ".html"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_render_html(title, summary, REQUIRE_REPORT))
    except OSError as e:
        return f"Error: could not save to {path}: {e}"   # not final: the model may try another name
    raise StopAgent(f"Report saved to {path}")


REPORT_AGENT = Agent(
    "report-agent",
    "You write reports about a computer from system data you are given. "
    "Write a clear title and a 2-4 sentence summary of notable findings "
    "(for example low disk space, high memory use, stopped automatic services), "
    "choose a sensible file name, then call save_html_report exactly once. "
    "Do not list the data yourself; the tool builds the tables.",
    [save_html_report],
)


def handoff_message() -> str:
    previews = "\n\n".join(preview(section, rows) for section, rows in REQUIRE_REPORT.items())
    return f"Create an HTML report from this system data (previews shown; the tool has all rows):\n\n{previews}"
