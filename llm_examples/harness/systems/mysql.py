"""MySQL-specific knowledge: mysql.connector prompt instructions. Kept out of
generate.py so that file stays generic pipeline/prompt-assembly logic instead of
accumulating per-system business knowledge -- see systems/__init__.py.
"""

from systems.config_format import CONFIG_FORMAT_INSTRUCTION

NAME = "MySQL"


def matches(external_system: str) -> bool:
    return "mysql" in external_system.lower()


NEEDS_CONFIG_FILE = True

SOURCE_INSTRUCTION = (
    "If the task involves a MySQL database via mysql.connector, the config file's credential keys "
    "must be named exactly 'user' and 'password' (matching mysql.connector.connect()'s keyword "
    "arguments), never 'admin_username' or other names -- so the config section can be passed "
    "straight into connect(**config) without renaming keys. Always include both a 'user' key and a "
    "'password' key in the config file; never omit the password. " + CONFIG_FORMAT_INSTRUCTION
)

TEST_INSTRUCTION = (
    "Any test database or test user the code creates against a real MySQL server must have a name "
    "unique to that run -- suffix it with a timestamp (e.g. f'test_db_{int(time.time())}'), never a "
    "fixed literal like 'test_db'. This server persists between runs, so a fixed name collides with "
    "whatever a previous run's test left behind (e.g. it crashed before its own cleanup ran) with a "
    "'database exists' error that has nothing to do with whether this run's code is correct."
)

AUTOFIXES = []
