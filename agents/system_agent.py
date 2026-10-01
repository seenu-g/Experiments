"""
System agent: looks up system info, installed software and services
(plus the calculator/time/notes tools from simple_agent.py).

Output of the 3 system tools is stored in REQUIRE_REPORT for the report agent.
"""

import platform
import socket
import sys
from datetime import datetime

import psutil

from agent import Agent
from simple_agent import calculator, get_current_time, read_notes, save_note

PREVIEW_ROWS = 15      # rows of each data set the models actually see

# Full output of the 3 system tools for the current turn, keyed by section name.
# The models only see a preview; the HTML report is built from this.
# Cleared with .clear() each turn - never reassign, report_agent.py imports this same dict.
REQUIRE_REPORT: dict[str, list[dict]] = {}


def preview(section: str, rows: list[dict]) -> str:
    lines = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in rows[:PREVIEW_ROWS]]
    if len(rows) > PREVIEW_ROWS:
        lines.append(f"... {len(rows) - PREVIEW_ROWS} more rows not shown (showing {PREVIEW_ROWS} of "
                     f"{len(rows)}); the full list goes in the HTML report. Do not guess them.")
    return f"{section} ({len(rows)} rows):\n" + "\n".join(lines)


# Search only the columns that identify an item (its name), case-insensitive.
# Publisher/status are properties, not identity: "Microsoft" would hit ~200 programs.
def _match(rows: list[dict], term: str, cols: tuple) -> list[dict]:
    needle = term.lower()
    return [r for r in rows if any(needle in str(r.get(c, "")).lower() for c in cols)]


# name_filter may hold several names ("Chrome, FFmpeg"). Each name gets its own answer line,
# so a miss on one name can't be read as a miss on all of them.
def _record(section: str, rows: list[dict], name_filter: str | None = None, cols: tuple = ("Name",)) -> str:
    if not name_filter:
        REQUIRE_REPORT[section] = rows
        return preview(section, rows)

    terms = [t.strip() for t in name_filter.split(",") if t.strip()]
    if len(terms) == 1 and " " in terms[0] and not _match(rows, terms[0], cols):
        terms = terms[0].split()                   # model packed several names without commas
    found, parts = [], []
    for term in terms:
        hits = _match(rows, term, cols)
        parts.append(preview(f"{section} matching '{term}'", hits) if hits
                     else f"No {section.lower()} matching '{term}'.")
        found += [r for r in hits if r not in found]
    if found:
        REQUIRE_REPORT[f"{section} matching '{', '.join(terms)}'"] = found
    return "\n\n".join(parts)


def get_system_info() -> str:
    """Get hardware and OS details of this computer: OS, CPU, memory, disks, uptime."""
    mem = psutil.virtual_memory()
    info = {
        "Hostname": socket.gethostname(),
        "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
        "Architecture": platform.machine(),
        "Processor": platform.processor() or "unknown",
        "CPU cores": f"{psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical",
        "Memory": f"{mem.total / 2**30:.1f} GB total, {mem.percent}% used",
        "Last boot": datetime.fromtimestamp(psutil.boot_time()).strftime("%d %B %Y, %H:%M"),
    }
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except OSError:                            # empty card readers, DVD drives, etc.
            continue
        info[f"Disk {part.device}"] = f"{usage.total / 2**30:.0f} GB, {usage.percent}% used"
    return _record("System information", [{"Property": k, "Value": v} for k, v in info.items()])


def _reg_value(key, name: str) -> str:
    import winreg
    try:
        return str(winreg.QueryValueEx(key, name)[0])
    except OSError:
        return ""


def get_installed_software(name_filter: str | None = None) -> str:
    """List software installed on this computer with version and publisher.

    Args:
        name_filter: Optional name(s) to search for. Several names: separate with commas, e.g. 'Chrome, FFmpeg'. Leave empty to list everything.
    """
    if sys.platform != "win32":
        return "Error: installed-software listing is only implemented for Windows."
    import winreg
    uninstall_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    found = {}
    for hive, path in uninstall_keys:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue
        with root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, i)) as sub:
                        name = _reg_value(sub, "DisplayName")
                        if name:
                            version = _reg_value(sub, "DisplayVersion")
                            found[(name, version)] = {
                                "Name": name, "Version": version,
                                "Publisher": _reg_value(sub, "Publisher"),
                            }
                except OSError:
                    continue
    rows = sorted(found.values(), key=lambda r: r["Name"].lower())
    return _record("Installed software", rows, name_filter)


def get_services(name_filter: str | None = None) -> str:
    """List the services on this computer with their status and start type.

    Args:
        name_filter: Optional name(s) to search for. Several names: separate with commas, e.g. 'BITS, WSearch'. Leave empty to list everything.
    """
    if sys.platform != "win32":
        return "Error: service listing is only implemented for Windows."
    rows = []
    for svc in psutil.win_service_iter():
        try:
            rows.append({
                "Name": svc.name(), "Display name": svc.display_name(),
                "Status": svc.status(), "Start type": svc.start_type(),
            })
        except psutil.Error:                       # service vanished or access denied
            continue
    rows.sort(key=lambda r: r["Name"].lower())
    return _record("Services", rows, name_filter, cols=("Name", "Display name"))


SYSTEM_AGENT = Agent(
    "system-agent",
    "You are a helpful assistant with tools for inspecting this computer. "
    "get_system_info is for hardware and OS (CPU, memory, disks). "
    "get_installed_software is for programs and their versions (e.g. Python, Git). "
    "get_services is for Windows services. "
    "ALWAYS call the tool for these questions, even if the conversation mentioned it before: "
    "the machine changes, so earlier answers may be outdated. "
    "When asked about specific services or programs, pass their names as name_filter, comma-separated. "
    "Tool results may show only the first rows. Only mention items that appear in the tool "
    "result - never add names you did not see. If rows were cut off, say how many were shown "
    "out of the total and that the full list is in the HTML report. "
    "Use the calculator for every calculation. Use tools only when needed. "
    "After getting tool results, give the user a short, clear answer. "
    "When the answer has more than one item, put each item on its own line starting with '- ', "
    "for example:\n- Copilot 154.0 - installed\n- FFmpeg 9.0 - installed\n- Firefox - not installed",
    [get_system_info, get_installed_software, get_services,
     calculator, get_current_time, save_note, read_notes],
)
