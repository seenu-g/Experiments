"""
eval_setup_db.py — Confirm setup_db.py built the hr_agent database correctly.

Run after setup:  python setup_db.py && python eval_setup_db.py

Checks tables, columns, indexes, foreign keys, constraints, reporting lines and seeded data.
Expected values live in eval_expected.py.
Read-only: the constraint checks try bad writes inside savepoints and roll them back.
Exit code 0 = all checks passed, 1 = something is missing or wrong.
"""

import sys

import psycopg2

from config import DB_CONFIG
from eval_expected import (EXPECTED_COLUMNS, EXPECTED_FKS, EXPECTED_INDEXES, EXPECTED_ROWS,
                           NULLABLE_FKS, REMOVED_COLUMNS, SALARY_RANGES)

results = []                                       # (passed, message)


def check(passed: bool, message: str) -> None:
    results.append((passed, message))
    print(f"  {'PASS' if passed else 'FAIL'}  {message}")


def check_tables(cur) -> set:
    cur.execute("SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
    found = {r[0] for r in cur.fetchall()}
    for table in EXPECTED_COLUMNS:
        check(table in found, f"table {table} exists")
    return found


def check_columns(cur, tables: set) -> None:
    for table, expected in EXPECTED_COLUMNS.items():
        if table not in tables:
            continue                               # already reported as missing
        cur.execute("SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s", (table,))
        found = {r[0] for r in cur.fetchall()}
        missing = [c for c in expected if c not in found]
        check(not missing, f"{table} has all {len(expected)} columns"
              + (f" (missing: {', '.join(missing)})" if missing else ""))
        for t, column in REMOVED_COLUMNS:
            if t == table:
                check(column not in found, f"{table}.{column} is removed (redundant)")


def check_indexes(cur) -> None:
    cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    found = {r[0] for r in cur.fetchall()}
    for index in sorted(EXPECTED_INDEXES):
        check(index in found, f"index {index} exists")


def check_foreign_keys(cur) -> None:
    cur.execute("""
        SELECT kcu.table_name, kcu.column_name, ccu.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
    """)
    found = {(t, c): ref for t, c, ref in cur.fetchall()}
    for (table, column), ref in EXPECTED_FKS.items():
        check(found.get((table, column)) == ref, f"{table}.{column} -> {ref}")

    # A foreign key column that allows NULL lets rows exist without the thing they belong to.
    cur.execute("SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND is_nullable = 'YES'")
    nullable = set(cur.fetchall())
    for table, column in EXPECTED_FKS:
        if (table, column) not in NULLABLE_FKS:
            check((table, column) not in nullable, f"{table}.{column} is NOT NULL")


# Reporting lines: exactly one manager per department with staff; everyone else reports to
# their own department's manager; managers report to nobody. is_manager must agree with that.
def check_managers(cur) -> None:
    queries = {
        "every department with staff has exactly one manager":
            "SELECT COUNT(*) FROM (SELECT dept_id FROM employee GROUP BY dept_id "
            "HAVING COUNT(*) FILTER (WHERE is_manager) <> 1) x",
        "every non-manager reports to their own department's manager":
            "SELECT COUNT(*) FROM employee e LEFT JOIN employee m ON m.emp_id = e.manager_id "
            "WHERE NOT e.is_manager AND (m.emp_id IS NULL OR NOT m.is_manager OR m.dept_id <> e.dept_id)",
        "managers report to nobody":
            "SELECT COUNT(*) FROM employee WHERE is_manager AND manager_id IS NOT NULL",
    }
    for message, query in queries.items():
        cur.execute("SAVEPOINT managers")
        try:
            cur.execute(query)
            bad = cur.fetchone()[0]
            check(bad == 0, f"{message} ({bad} violations)")
        except psycopg2.Error as e:                # e.g. manager_id missing
            cur.execute("ROLLBACK TO SAVEPOINT managers")
            check(False, f"{message} (could not test: {e.pgerror.splitlines()[0] if e.pgerror else e})")


# Rules the database must enforce by itself: inserting a bad row has to fail.
# Each attempt runs inside a savepoint and is rolled back, so no data is changed.
def check_constraints(cur) -> None:
    attempts = {
        "second current salary for one employee is rejected":
            "INSERT INTO employee_salary(emp_id, amount, effective_date, is_current) "
            "SELECT emp_id, 1000, CURRENT_DATE, TRUE FROM employee_salary WHERE is_current LIMIT 1",
        "salary amount <= 0 is rejected":
            "INSERT INTO employee_salary(emp_id, amount, effective_date, is_current) "
            "SELECT emp_id, -1, CURRENT_DATE, FALSE FROM employee LIMIT 1",
        "unknown level is rejected":
            "UPDATE employee SET level = 'Wizard' WHERE emp_id = (SELECT MIN(emp_id) FROM employee)",
        "duplicate department name in one org is rejected":
            "INSERT INTO department(org_id, name) SELECT org_id, name FROM department LIMIT 1",
    }
    for message, statement in attempts.items():
        cur.execute("SAVEPOINT attempt")
        rejected, note = False, ""
        try:
            cur.execute(statement)                 # succeeding here means the rule is missing
        except psycopg2.IntegrityError:            # the constraint did its job
            rejected = True
        except psycopg2.Error as e:                # e.g. column missing: can't test, count as FAIL
            rejected, note = False, f" (could not test: {e.pgerror.splitlines()[0] if e.pgerror else e})"
        cur.execute("ROLLBACK TO SAVEPOINT attempt")
        check(rejected, message + note)


def check_rows(cur, tables: set) -> None:
    counts = {}
    for table in EXPECTED_COLUMNS:
        if table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")   # table names come from our own constant
            counts[table] = cur.fetchone()[0]
    for table, (lo, hi) in EXPECTED_ROWS.items():
        n = counts.get(table, 0)
        want = str(lo) if lo == hi else f"{lo}-{hi}"
        check(lo <= n <= hi, f"{table} has {n} rows (expected {want})")

    # Each employee gets exactly 2 salary rows: one historical, one current.
    employees = counts.get("employee", 0)
    check(counts.get("employee_salary", 0) == 2 * employees,
          f"employee_salary has {counts.get('employee_salary', 0)} rows (expected 2 x {employees})")
    if "employee_salary" in tables:
        cur.execute("SELECT COUNT(*) FROM employee e WHERE (SELECT COUNT(*) FROM employee_salary s "
                    "WHERE s.emp_id = e.emp_id AND s.is_current) <> 1")
        bad = cur.fetchone()[0]
        check(bad == 0, f"every employee has exactly one current salary ({bad} do not)")

        # Current salary must fit the employee's own level (the old seed picked levels at random).
        cur.execute("SAVEPOINT ranges")
        try:
            cur.execute("SELECT e.level, s.amount FROM employee e "
                        "JOIN employee_salary s ON s.emp_id = e.emp_id AND s.is_current")
            outside = [(lvl, amt) for lvl, amt in cur.fetchall()
                       if lvl not in SALARY_RANGES or not SALARY_RANGES[lvl][0] <= amt <= SALARY_RANGES[lvl][1]]
            check(not outside, f"every current salary is within its level's range ({len(outside)} are not)")
        except psycopg2.Error as e:                # e.g. employee.level missing
            cur.execute("ROLLBACK TO SAVEPOINT ranges")
            check(False, f"every current salary is within its level's range (could not test: {e.pgerror.splitlines()[0] if e.pgerror else e})")


def main() -> int:
    print(f"\nEvaluating database {DB_CONFIG['database']} on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("-" * 50)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"  FAIL  cannot connect: {e}")
        return 1

    with conn, conn.cursor() as cur:
        print("\nTables");       tables = check_tables(cur)
        print("\nColumns");      check_columns(cur, tables)
        print("\nIndexes");      check_indexes(cur)
        print("\nForeign keys"); check_foreign_keys(cur)
        print("\nConstraints");  check_constraints(cur)
        print("\nManagers");     check_managers(cur)
        print("\nSeeded data");  check_rows(cur, tables)
        conn.rollback()                            # the eval never changes data
    conn.close()

    failed = [m for ok, m in results if not ok]
    print("-" * 50)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:\n  " + "\n  ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
