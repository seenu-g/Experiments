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
import os

_BUILTIN_NAMES = set(dir(builtins)) | {"__name__", "__file__", "__doc__"}


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


def check_resolve_issues(py_paths: list) -> tuple[bool, str]:
    """Runs all static resolution checks and combines every issue any of them
    finds into a single failure detail, so one retry can address all of them
    instead of discovering them one at a time across multiple attempts."""
    issues = (
        check_undefined_module_references(py_paths)
        + check_undefined_module_usage(py_paths)
        + check_undefined_function_calls(py_paths)
    )
    if not issues:
        return True, ""
    return False, "\n".join(issues)
