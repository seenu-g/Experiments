"""LINT stage: pure syntax validation via ast.parse(). No side effects."""

import ast


def lint_files(paths: list) -> tuple[bool, str]:
    """Returns (passed, detail). detail is '' on pass, the first error text on fail."""
    for path in paths:
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source, filename=path)
        except SyntaxError as e:
            return False, f"Lint (ast.parse) failed on {path}: {e}"
    return True, ""
