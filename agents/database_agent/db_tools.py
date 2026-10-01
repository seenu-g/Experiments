"""
db_tools.py — Tool functions the HR agent's code runs against the database.

These are the only operations the agent can perform on the database.
What the model is told about them lives in tool_definitions.py and db_schema.py.
"""

import json
import psycopg2
import psycopg2.extras
from typing import Any

from config import DB_CONFIG
from db_schema import DB_SCHEMA

# ── DB connection ─────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


# ── Tool implementations ───────────────────────────────────────────────────────

def run_sql(query: str) -> str:
    """
    Execute a read-only SELECT query and return results as JSON.
    Raises if the query is not a SELECT (safety guard).
    """
    q = query.strip().upper()
    if not q.startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed via run_sql. Use disable_employee for writes."})
    try:
        with get_conn() as conn:
            # The prefix check above is only a friendly message; "SELECT 1; UPDATE ..." passes it.
            # A read-only session makes PostgreSQL itself reject any write.
            conn.set_session(readonly=True)
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                # RealDictCursor rows → list of plain dicts
                result = [dict(r) for r in rows]
                if not result:
                    # An empty result only means THIS query matched nothing - the model tends to
                    # read it as "that person doesn't exist". Say plainly what it does and doesn't mean.
                    return json.dumps({"message": "No rows matched this query. That does not prove the person "
                                                  "or thing doesn't exist: a JOIN or filter may have excluded it. "
                                                  "Check the query (e.g. JOIN vs LEFT JOIN) before concluding.",
                                       "rows": []})
                return json.dumps({"rows": result, "count": len(result)}, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Fuzzy search by name (first, last or full); shared by find_employee and disable_employee.
def _search_employees(name: str) -> list[dict]:
    query = """
        SELECT e.emp_id,
               e.first_name || ' ' || e.last_name AS full_name,
               d.name AS department,
               e.is_active,
               e.is_manager
        FROM employee e
        JOIN department d ON e.dept_id = d.dept_id
        WHERE LOWER(e.first_name || ' ' || e.last_name) LIKE LOWER(%s)
           OR LOWER(e.first_name) LIKE LOWER(%s)
           OR LOWER(e.last_name)  LIKE LOWER(%s)
        ORDER BY e.is_active DESC, full_name
        LIMIT 10
    """
    pattern = f"%{name}%"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (pattern, pattern, pattern))
            return [dict(r) for r in cur.fetchall()]


def find_employee(name: str) -> str:
    """Fuzzy search employees by name. Returns emp_id, full name, department, active status."""
    try:
        rows = _search_employees(name)
    except Exception as e:
        return json.dumps({"error": str(e)})
    if not rows:
        return json.dumps({"message": f"No employee found matching '{name}'."})
    return json.dumps({"matches": rows, "count": len(rows)}, default=str)


# The model's tool: it only REQUESTS a disable. Nothing is written here; the agent code asks
# the user and calls confirm_disable() itself on "yes" - the model cannot skip that step.
# The model must give a NAME. Code looks it up; an emp_id is only accepted if it belongs to
# one of the employees matching that name - so an id reused from history or invented is rejected.
def disable_employee(name: str, emp_id: int | None = None) -> str:
    if not name.strip():
        return json.dumps({"error": "name is required: give the employee's name, not only an emp_id."})
    try:
        matches = _search_employees(name)
    except Exception as e:
        return json.dumps({"error": str(e)})
    if not matches:
        return json.dumps({"error": f"No employee found matching '{name}'."})

    if emp_id is not None:
        chosen = [m for m in matches if m["emp_id"] == emp_id]
        if not chosen:
            return json.dumps({"error": f"emp_id {emp_id} is not an employee matching '{name}'. "
                                        "Do not reuse ids from earlier answers.",
                               "matches": matches}, default=str)
        person = chosen[0]
    else:
        active = [m for m in matches if m["is_active"]]
        if not active:
            return json.dumps({"message": f"Everyone matching '{name}' is already inactive."})
        if len(active) > 1:
            return json.dumps({"message": f"{len(active)} active employees match '{name}'. Ask the user which "
                                          "one, then call disable_employee again with name and their emp_id.",
                               "matches": active}, default=str)
        person = active[0]

    if not person["is_active"]:
        return json.dumps({"message": f"{person['full_name']} is already inactive."})
    return json.dumps({
        "confirmation_required": True,
        "emp_id": person["emp_id"],
        "full_name": person["full_name"],
        "message": f"Disable {person['full_name']} ({person['department']}, emp_id={person['emp_id']})? "
                   "Reply yes or no.",
    })


# The actual write. Not in the dispatcher or TOOL_DEFINITIONS, so the model can never call it;
# only agent code calls it, after the user replied "yes".
def confirm_disable(emp_id: int) -> str:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT first_name || ' ' || last_name AS full_name, is_active FROM employee WHERE emp_id = %s",
                    (emp_id,)
                )
                row = cur.fetchone()
                if not row:
                    return json.dumps({"error": f"No employee with emp_id = {emp_id}"})

                full_name = row["full_name"]
                if not row["is_active"]:
                    return json.dumps({"message": f"{full_name} is already inactive."})

                cur.execute(
                    "UPDATE employee SET is_active = FALSE WHERE emp_id = %s",
                    (emp_id,)
                )
                conn.commit()
                return json.dumps({
                    "success": True,
                    "message": f"Employee '{full_name}' (emp_id={emp_id}) has been disabled.",
                })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_schema() -> str:
    """Return the database schema description."""
    return DB_SCHEMA


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def run_tool(name: str, args: dict) -> str:
    dispatch = {
        "run_sql":          lambda a: run_sql(a["query"]),
        "find_employee":    lambda a: find_employee(a["name"]),
        "disable_employee": lambda a: disable_employee(
            str(a.get("name") or ""), int(a["emp_id"]) if a.get("emp_id") not in (None, "") else None),
        "get_schema":       lambda a: get_schema(),
    }
    fn = dispatch.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    return fn(args)
