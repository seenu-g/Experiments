"""VALIDATE stage: check the generated code's runtime prerequisites before EXECUTE.

Only EXECUTE actually needs this. LINT (ast.parse) and COMPILE (py_compile) both
only parse/compile source -- neither one imports the modules it references or
opens the config files it reads, so a missing library or a placeholder
credential can't make either of them fail. It can only blow up at EXECUTE time,
so that's the only place this stage guards.

Runs against the staged stage_v<N>/ copy (original filenames, the ones EXECUTE
actually reads), never the versioned run_dir/ save -- that save stays an
untouched historical record of exactly what the model produced.
"""

import ast
import configparser
import importlib.util
import os
import re
import subprocess
import sys

from config import VALIDATE_TIMEOUT_SECONDS
from timeout_input import InputTimeout, confirm_with_timeout, input_with_timeout

_PLACEHOLDER_MARKERS = ("password", "changeme", "your_", "xxx", "example", "<", "todo")

# Matches a whole line that's just one credential-looking assignment with a
# *quoted* (string-literal) value, e.g. `password = 'abc123'` or
# `    'user': 'your_username',`. Requiring the value to be quoted is what
# keeps this from matching a kwarg/variable reference like `user=admin_username,`
# -- an unquoted value there is a name lookup, not a literal to fix.
_PY_CRED_LINE_RE = re.compile(
    r"^[ \t]*(?P<qkey>['\"]?)(?P<key>user|username|admin_username|password|passwd|pwd|secret|token|"
    r"api[_-]?key|aws_access_key_id|aws_secret_access_key)"
    r"(?P=qkey)\s*[:=]\s*(?P<vquote>['\"])(?P<value>[^'\"\n]*)(?P=vquote)\s*,?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def find_missing_libraries(py_paths: list) -> list:
    """Return the top-level third-party import names used by these files that
    aren't importable in the current environment."""
    names = set()
    for path in py_paths:
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])

    local_modules = {os.path.splitext(os.path.basename(p))[0] for p in py_paths}
    missing = []
    for name in sorted(names - local_modules):
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    return missing


def find_placeholder_config_values(non_py_paths: list, external_system: str = "") -> dict:
    """Return {path: [(section, key, value), ...]} for .ini values that need a human
    to confirm/supply them before EXECUTE: empty values, values that look like a
    placeholder the model invented, or -- for MySQL tasks, 'user'/'password'; for AWS
    tasks, 'aws_access_key_id'/'aws_secret_access_key' -- checked unconditionally since
    a fake-but-plausible value like 'abc123' or 'AKIAIOSFODNN7EXAMPLE' won't match any
    placeholder marker, and there's no point letting EXECUTE run against AWS/a real
    database with a credential nobody actually supplied."""
    always_flag_keys = set()
    if "mysql" in external_system.lower():
        always_flag_keys |= {"user", "password"}
    if "aws" in external_system.lower():
        always_flag_keys |= {"aws_access_key_id", "aws_secret_access_key"}
    findings = {}
    for path in non_py_paths:
        if not path.endswith(".ini"):
            continue
        parser = configparser.ConfigParser()
        parser.read(path)
        flagged = [
            (section, key, value)
            for section in parser.sections() or ["DEFAULT"]
            for key, value in parser[section].items()
            if not value.strip()
            or key.lower() in always_flag_keys
            or any(marker in value.lower() for marker in _PLACEHOLDER_MARKERS)
        ]
        if flagged:
            findings[path] = flagged
    return findings


def find_placeholder_credentials_in_py(py_paths: list, external_system: str = "") -> list:
    """Return [(path, key, value, value_start, value_end), ...] for .py files with
    quoted credential-literal assignments that need a human to confirm/supply them --
    the model sometimes writes credentials into a plain Python config module (e.g.
    `config = {'user': 'your_username', 'password': 'your_password'}`) instead of an
    .ini file, which find_placeholder_config_values never looks at."""
    always_flag_keys = set()
    if "mysql" in external_system.lower():
        always_flag_keys |= {"user", "username", "password"}
    if "aws" in external_system.lower():
        always_flag_keys |= {"aws_access_key_id", "aws_secret_access_key"}
    findings = []
    for path in py_paths:
        with open(path) as f:
            content = f.read()
        for m in _PY_CRED_LINE_RE.finditer(content):
            key = m.group("key").lower()
            value = m.group("value")
            if (
                not value.strip()
                or key in always_flag_keys
                or any(marker in value.lower() for marker in _PLACEHOLDER_MARKERS)
            ):
                findings.append((path, key, value, m.start("value"), m.end("value")))
    return findings


def validate_environment(
    py_paths: list,
    non_py_paths: list,
    logger,
    external_system: str = "",
    timeout: float = VALIDATE_TIMEOUT_SECONDS,
) -> tuple[bool, str]:
    """Returns (ok_to_execute, detail). Nothing here raises to the caller: a 'no',
    a blank answer, or no response within `timeout` seconds are all treated the
    same way -- EXECUTE (and the whole run) can't proceed, but the failure is
    reported, not thrown."""
    for lib in find_missing_libraries(py_paths):
        try:
            if not confirm_with_timeout(
                f"Library '{lib}' is not installed. Install it now via pip?", timeout
            ):
                return False, f"Library '{lib}' not installed; user declined to install."
        except InputTimeout:
            return False, (
                f"Library '{lib}' not installed and no response within {timeout:.0f}s. "
                f"Install it (pip install {lib}) and rerun the harness."
            )
        logger.info(f"Installing missing library: {lib}")
        subprocess.run([sys.executable, "-m", "pip", "install", lib], check=False)
        if importlib.util.find_spec(lib) is None:
            return False, f"Library '{lib}' still not importable after install attempt."

    for path, flagged in find_placeholder_config_values(non_py_paths, external_system).items():
        parser = configparser.ConfigParser()
        parser.read(path)
        for section, key, old_value in flagged:
            try:
                new_value = input_with_timeout(
                    f"{os.path.basename(path)} [{section}] {key} looks like a placeholder "
                    f"('{old_value}') -- enter the real value: ",
                    timeout,
                ).strip()
            except InputTimeout:
                return False, (
                    f"No response within {timeout:.0f}s for [{section}] {key} in "
                    f"{os.path.basename(path)}. Fill it in and rerun the harness."
                )
            if not new_value:
                return False, f"No real value supplied for [{section}] {key} in {os.path.basename(path)}."
            parser[section][key] = new_value
        with open(path, "w") as f:
            parser.write(f)
        logger.info(f"Updated credentials in {path} from user input.")

    py_findings: dict = {}
    for path, key, old_value, start, end in find_placeholder_credentials_in_py(py_paths, external_system):
        py_findings.setdefault(path, []).append((key, old_value, start, end))

    for path, flagged in py_findings.items():
        with open(path) as f:
            content = f.read()
        # Replace from the end of the file backward so earlier spans stay valid
        # as later-in-file replacements change the string length.
        for key, old_value, start, end in sorted(flagged, key=lambda item: item[2], reverse=True):
            try:
                new_value = input_with_timeout(
                    f"{os.path.basename(path)}: '{key}' looks like a placeholder "
                    f"('{old_value}') -- enter the real value: ",
                    timeout,
                ).strip()
            except InputTimeout:
                return False, (
                    f"No response within {timeout:.0f}s for '{key}' in "
                    f"{os.path.basename(path)}. Fill it in and rerun the harness."
                )
            if not new_value:
                return False, f"No real value supplied for '{key}' in {os.path.basename(path)}."
            content = content[:start] + new_value + content[end:]
        with open(path, "w") as f:
            f.write(content)
        logger.info(f"Updated credentials in {path} from user input.")

    return True, ""
