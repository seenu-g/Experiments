"""RESOLVE check: catch hallucinated cross-file (or self-) references and
missing imports before COMPILE/EXECUTE waste a cycle on them.

Purely static and deterministic -- like LINT and COMPILE, it never imports or
runs anything, so it doesn't need VALIDATE's environment. Unlike VALIDATE's
checks, a failure here IS something regenerated code can fix (the model just
needs to actually define or import the thing it's using), so it retries like
a LINT/COMPILE failure rather than stopping the run.

Regression case #1: an entrypoint that was

    import test_database_manager
    test_database_manager.TestDatabaseManager().run()

-- a self-import expecting a class that was never defined anywhere (not in
this file, not in any sibling generated file). LINT (ast.parse) and COMPILE
(py_compile) both passed it -- it's syntactically valid Python -- and it only
failed at EXECUTE with `AttributeError: partially initialized module
'test_database_manager' has no attribute 'TestDatabaseManager'`.

Regression case #2: the same file separately used `mysql.connector.Error`
and `time.time()` without importing either. The two sub-checks below used to
each return on their *first* match, so a single retry only ever learned about
one problem at a time -- the model fixed the reported one, the retry
surfaced the next one, and the run burned its whole attempt budget without
ever reaching EXECUTE. Both checks now collect every issue they find so a
single retry can address all of them at once.
"""

import ast
import builtins
import importlib.util
import os
import re
import sys

_BUILTIN_NAMES = set(dir(builtins)) | {"__name__", "__file__", "__doc__"}
_STDLIB_DIR = os.path.dirname(os.__file__)


def _module_stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _top_level_defs(tree: ast.AST) -> set:
    """Names defined at module level: functions, classes, and simple assignments."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def check_undefined_module_references(py_paths: list) -> list:
    """For every `import X` in a generated file (X being another generated file,
    or itself via a self-import), check that any `X.attr(...)` call actually
    refers to something defined at module level in X.py. Third-party/stdlib
    imports (e.g. `sqlite3.connect(...)`) are naturally out of scope -- X only
    matches here when X.py is one of the files this run generated.

    Returns every distinct issue found (possibly empty), not just the first."""
    defs_by_module = {}
    trees_by_path = {}
    for path in py_paths:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
        trees_by_path[path] = tree
        defs_by_module[_module_stem(path)] = _top_level_defs(tree)

    issues = []
    seen = set()
    for path, tree in trees_by_path.items():
        imported_modules = {
            alias.asname or alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            callee = node.func.value
            if not isinstance(callee, ast.Name):
                continue
            module_name = callee.id
            if module_name not in imported_modules or module_name not in defs_by_module:
                continue
            attr = node.func.attr
            if attr not in defs_by_module[module_name]:
                key = (path, module_name, attr)
                if key in seen:
                    continue
                seen.add(key)
                issues.append(
                    f"{os.path.basename(path)} calls {module_name}.{attr}(...), but "
                    f"'{attr}' is never defined in {module_name}.py."
                )

    return issues


def _all_defined_names(tree: ast.AST) -> set:
    """Every name assigned, imported, or bound anywhere in this file (functions,
    classes, variables, function params, for-loop/with/comprehension targets,
    global/nonlocal declarations) -- a flat, scope-blind union. This isn't full
    scope analysis (a name used before its actual definition in execution order
    would slip through), but it's enough to answer 'is this name defined
    ANYWHERE in this file' without false-flagging legitimately scoped names."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
    return names


def check_undefined_module_usage(py_paths: list) -> list:
    """Catch a name used as `X.attr(...)` where X is never imported, assigned,
    or otherwise defined anywhere in the file -- e.g. calling time.time()
    without `import time`. Neither ast.parse nor py_compile resolve names, so
    this slips past LINT/COMPILE and would otherwise only surface as a
    NameError at EXECUTE.

    Returns every distinct issue found (possibly empty), not just the first."""
    issues = []
    for path in py_paths:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
        defined = _all_defined_names(tree) | _BUILTIN_NAMES

        seen = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and isinstance(node.value.ctx, ast.Load)
                and node.value.id not in defined
            ):
                key = (path, node.value.id)
                if key in seen:
                    continue
                seen.add(key)
                issues.append(
                    f"{os.path.basename(path)} uses '{node.value.id}.{node.attr}', but "
                    f"'{node.value.id}' is never imported or defined anywhere in this file."
                )

    return issues


def _is_stdlib_module(name: str) -> bool:
    """True only for a genuine, importable Python stdlib module -- never a
    third-party package. sys.stdlib_module_names (3.10+) is the fast, exact
    path; find_spec's origin is the fallback/cross-check, restricted to files
    that live under the interpreter's own stdlib directory (so a same-named
    site-packages module never gets misclassified as stdlib)."""
    if name in getattr(sys, "stdlib_module_names", ()):
        return True
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError, ModuleNotFoundError):
        return False
    if spec is None or not spec.origin:
        return False
    return spec.origin.startswith(_STDLIB_DIR) and "site-packages" not in spec.origin


def autofix_stdlib_module_imports(files: list) -> tuple[list, list[str]]:
    """Deterministically fix ONE narrow, unambiguous class of check_undefined_module_usage
    finding: a bare `X.attr` usage (e.g. time.time()) where X is missing from the file but
    IS a genuine Python stdlib module. 'import X' is the only possible correct fix in that
    case -- unlike an ambiguous cross-file reference (check_undefined_function_calls, where
    RESOLVE can't know which sibling file to import from), there's nothing for a regenerate
    -and-retry attempt to usefully decide here, so this patches the file in place instead of
    spending one of the run's limited attempts on it.

    Runs on the in-memory (filename, code) pairs BEFORE save/stage, so the fix is reflected
    consistently in both the versioned save and the staged copy everything downstream uses.
    A file with a syntax error is left untouched -- LINT will catch and report that as usual.

    Returns (fixed_files, fix_descriptions) -- fixed_files is the same shape as the input,
    fix_descriptions is a human-readable line per import added (possibly empty)."""
    fixed_files = []
    fixes = []
    for filename, code in files:
        if not filename.endswith(".py"):
            fixed_files.append((filename, code))
            continue

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError:
            fixed_files.append((filename, code))
            continue

        defined = _all_defined_names(tree) | _BUILTIN_NAMES
        missing_modules = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and isinstance(node.value.ctx, ast.Load)
                and node.value.id not in defined
                and _is_stdlib_module(node.value.id)
            ):
                missing_modules.add(node.value.id)

        if missing_modules:
            code = "".join(f"import {name}\n" for name in sorted(missing_modules)) + code
            fixes.extend(f"{filename}: auto-added missing 'import {name}'" for name in sorted(missing_modules))

        fixed_files.append((filename, code))

    return fixed_files, fixes


def check_undefined_function_calls(py_paths: list) -> list:
    """Catch a bare call `foo(...)` where `foo` is never imported, defined, or
    otherwise bound anywhere in the file -- e.g. a test file calling
    create_s3_bucket(...) without ever doing `from s3_manager import
    create_s3_bucket`. This is the same "used but never imported" problem
    check_undefined_module_usage catches, just for a plain name instead of a
    `module.attr` access -- neither ast.parse nor py_compile resolve names, so
    this slips past LINT/COMPILE and would otherwise only surface as a
    NameError at EXECUTE.

    This only checks whether the name is defined SOMEWHERE in the SAME file
    (imports, local defs, params, etc.) -- not whether it's importable from a
    sibling generated file. That's intentional: the actionable fix is "you
    forgot the import," not "does this function exist anywhere in this run"
    (check_undefined_module_references already covers cross-file module.attr()
    references).

    Returns every distinct issue found (possibly empty), not just the first."""
    issues = []
    for path in py_paths:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
        defined = _all_defined_names(tree) | _BUILTIN_NAMES

        seen = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and isinstance(node.func.ctx, ast.Load)
                and node.func.id not in defined
            ):
                key = (path, node.func.id)
                if key in seen:
                    continue
                seen.add(key)
                issues.append(
                    f"{os.path.basename(path)} calls '{node.func.id}(...)', but "
                    f"'{node.func.id}' is never imported or defined anywhere in this file."
                )

    return issues


_INI_READ_RE = re.compile(r"\.read\(\s*['\"](?P<fname>[^'\"]+\.ini)['\"]")


def check_missing_config_file_references(py_paths: list, generated_non_py_filenames: set) -> list:
    """Catch generated code that calls configparser's `.read('some.ini')` for a
    config file that was never actually generated in this attempt.

    configparser.read() doesn't raise FileNotFoundError for a missing file -- it
    silently returns an empty list of successfully-read files and the call
    becomes a no-op, leaving the parser's sections/keys empty. Nothing fails
    until later code does config['DEFAULT']['region'] and gets a plain KeyError,
    deep inside EXECUTE, that gives no hint the actual problem is a missing
    file (regression case: the 2026-08-13 20260813_013836 run's ec2_manager.py/
    s3_manager.py both called config.read('db_config.ini') across all 3
    attempts, but the model never once included a FILE block for db_config.ini
    -- VALIDATE's placeholder-credential checks only inspect .ini files that
    WERE generated, so this slipped past every stage until EXECUTE's
    KeyError: 'region', burning the whole attempt budget without the model
    ever being told what was actually missing."""
    issues = []
    for path in py_paths:
        with open(path) as f:
            source = f.read()
        for match in _INI_READ_RE.finditer(source):
            fname = match.group("fname")
            if fname not in generated_non_py_filenames:
                issues.append(
                    f"{os.path.basename(path)} calls .read('{fname}'), but '{fname}' was "
                    f"never generated in this attempt -- configparser.read() silently does "
                    f"nothing for a missing file instead of raising, so this must be caught "
                    f"here rather than left to surface as a confusing KeyError at EXECUTE."
                )
    return issues


def check_resolve_issues(py_paths: list, generated_non_py_filenames: set | None = None) -> tuple[bool, str]:
    """Runs all static resolution checks and combines every issue any of them
    finds into a single failure detail, so one retry can address all of them
    instead of discovering them one at a time across multiple attempts.

    generated_non_py_filenames: basenames of every non-.py file this attempt
    actually generated (e.g. {'app_config.ini'}). Passing None skips
    check_missing_config_file_references entirely -- opt-in so existing
    callers that only care about the .py-to-.py checks are unaffected."""
    issues = (
        check_undefined_module_references(py_paths)
        + check_undefined_module_usage(py_paths)
        + check_undefined_function_calls(py_paths)
    )
    if generated_non_py_filenames is not None:
        issues += check_missing_config_file_references(py_paths, generated_non_py_filenames)
    if not issues:
        return True, ""
    return False, "\n".join(issues)
