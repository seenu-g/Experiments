"""COMPILE stage: bytecode compilation via py_compile. No side effects beyond
the .pyc cache py_compile itself writes."""

import py_compile


def compile_files(paths: list) -> tuple[bool, str]:
    """Returns (passed, detail). detail is '' on pass, the first error text on fail."""
    for path in paths:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            return False, f"Compile failed on {path}: {e}"
    return True, ""
