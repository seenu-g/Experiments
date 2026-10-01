"""
config.py — PostgreSQL connection settings shared by all scripts in this folder.

Edit here once; setup_db.py, db_tools.py and eval_setup_db.py all import it.
"""

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "hr_agent",
    "user":     "postgres",
    "password": "abc123",          # ← change if needed
}
