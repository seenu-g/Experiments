#  if you want a GUI
#   instead of scripting it: DB Browser for SQLite
#   (https://sqlitebrowser.org/) opens
#   chroma_db/chroma.sqlite3 directly and lets you
#   click through tables/browse data — often faster
#   than reading raw dumps once you already know the
#   shape from this script.

import sqlite3

DB_PATH = "./chroma_db/chroma.sqlite3"


def inspect_schema(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cur.fetchall()

    for table, ddl in tables:
        cur.execute("SELECT COUNT(*) FROM " + table)
        row_count = cur.fetchone()[0]
        print(f"=== {table} ({row_count} rows) ===")
        print(ddl)
        print()

    conn.close()


if __name__ == "__main__":
    inspect_schema()
