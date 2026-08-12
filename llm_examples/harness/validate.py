"""VALIDATE stage: check the generated code's runtime prerequisites before EXECUTE.

Only EXECUTE actually needs this. LINT (ast.parse) and COMPILE (py_compile) both
only parse/compile source -- neither one imports the modules it references or
opens the config files it reads, so a missing library or a placeholder
credential can't make either of them fail. It can only blow up at EXECUTE time,
so that's the only place this stage guards.

Runs against the staged _exec_v<N>/ copy (original filenames, the ones EXECUTE
actually reads), never the versioned run_dir/ save -- that save stays an
untouched historical record of exactly what the model produced.
"""

import ast
import configparser
import importlib.util
import os
import subprocess
import sys

from config import VALIDATE_TIMEOUT_SECONDS
from timeout_input import InputTimeout, confirm_with_timeout, input_with_timeout

_PLACEHOLDER_MARKERS = ("password", "changeme", "your_", "xxx", "example", "<", "todo")


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


def find_placeholder_config_values(non_py_paths: list) -> dict:
    """Return {path: [(section, key, value), ...]} for .ini files whose values
    look like placeholders the model invented rather than real credentials."""
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
            if any(marker in value.lower() for marker in _PLACEHOLDER_MARKERS)
        ]
        if flagged:
            findings[path] = flagged
    return findings


def validate_environment(
    py_paths: list, non_py_paths: list, logger, timeout: float = VALIDATE_TIMEOUT_SECONDS
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

    for path, flagged in find_placeholder_config_values(non_py_paths).items():
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

    return True, ""
