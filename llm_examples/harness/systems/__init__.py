"""Per-external-system knowledge (prompt instructions + deterministic autofixes),
kept out of the generic pipeline files (generate.py, resolve.py, plan.py) so those
stay Python/architecture-generic rather than accumulating AWS/MySQL/Ollama trivia.

Each system module exposes the same shape:
- NAME: str
- matches(external_system: str) -> bool
- NEEDS_CONFIG_FILE: bool
- SOURCE_INSTRUCTION: str
- TEST_INSTRUCTION: str | None
- AUTOFIXES: list[Callable[[list], tuple[list, list[str]]]]

generate.py/resolve.py/plan.py dispatch generically over ALL_SYSTEMS instead of
hardcoding per-system `if "x" in external_system.lower()` branches -- adding a new
system means adding one new module here and one line below, not touching any
pipeline file.
"""

from systems import aws, langchain, mysql, ollama

ALL_SYSTEMS = [aws, mysql, ollama, langchain]
