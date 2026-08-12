"""LINT stage: pure syntax validation via ast.parse(). No side effects."""

import ast


def lint_files(paths: list) -> tuple[bool, str]:
    """Returns (passed, detail). detail is '' on pass, the first error text on fail."""
    for path in paths:
        with open(path) as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as e:
            return False, f"Lint (ast.parse) failed on {path}: {e}"

        if not tree.body:
            # An empty file is syntactically valid, so every later check (COMPILE,
            # RESOLVE, EXECUTE) trivially passes it too -- `python empty_file.py`
            # just exits 0 with no error, so a blank entrypoint silently reports a
            # false SUCCESS instead of the model having produced no code at all.
            return False, (
                f"Lint failed on {path}: file is empty (or contains only comments/whitespace)."
            )
    return True, ""
