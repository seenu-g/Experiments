# HR Agent — Local AI + PostgreSQL

Natural language interface to an HR database.
Runs 100% locally: **Ollama + Hermes3 + PostgreSQL 18**.

## Stack

| Layer | Tech |
|---|---|
| LLM | Ollama + hermes3 |
| Agent loop | Python + ollama SDK |
| Database | PostgreSQL 18 |
| API | FastAPI + uvicorn |
| Data | Faker (synthetic) |

## Setup

### 1. Install Python dependencies

```bash
pip install psycopg2-binary faker ollama fastapi uvicorn
```

### 2. Edit DB password (if needed)

Open `config.py` — change `"password": "postgres"` to your PostgreSQL password. All scripts read it from there.

### 3. Create DB and seed data

```bash
python setup_db.py
```

Creates the `hr_agent` database with ~90 employees across 3 organizations.

### 4. Run

**Option A — Terminal chat**
```bash
python client.py
```

**Option B — FastAPI server**
```bash
uvicorn hr_api:app --reload --port 8000
```
Then open **http://localhost:8000/docs** for interactive Swagger UI.

---

## Example questions

```
List all managers
Who reports to the Engineering manager at Apex Fintech?
Show me the salary of managers in Engineering
What is the education of employees in the Data department?
How many active employees are there per department?
Which city has the most employees?
Show me all employees hired in the last 2 years
Disable employee [name]         ← agent asks for confirmation first
```

## API usage

```python
import requests

# Single question
r = requests.post("http://localhost:8000/chat", json={
    "message": "List all managers in Engineering",
    "session_id": "my-session"
})
print(r.json()["answer"])

# Reset conversation
requests.post("http://localhost:8000/reset", json={"session_id": "my-session"})
```

## Files

| File | Purpose |
|---|---|
| `config.py` | PostgreSQL connection settings (shared) |
| `logger.py` | Writes `agent_log.txt`: every question, model call (with tokens), tool call and answer |
| `setup_db.py` | Create schema + seed ~90 employees |
| `schema_sql.py` | SQL that creates the tables (run by setup_db.py) |
| `seed_data.py` | Seed values: organizations, cities, departments, educations, salary ranges |
| `eval_setup_db.py` | Verify tables, columns, indexes, FKs, constraints, managers and seed data after setup |
| `eval_expected.py` | The expected schema and seed values the eval checks against |
| `db_tools.py` | Tool functions the app runs (run_sql uses a read-only connection) |
| `tool_definitions.py` | Tool descriptions sent to the model (Ollama tool schemas) |
| `db_schema.py` | Schema description + tested example queries sent to the model |
| `hr_agent.py` | Core agent loop (used by CLI and API); enforces disable confirmation in code |
| `instructions.py` | Rules + schema sent to the model on every call |
| `history.py` | Curates what the model sees from earlier turns (last 5, old tool results removed) |
| `client.py` | Interactive terminal chat |
| `hr_api.py` | FastAPI REST + streaming API |

## Schema

```
organization ──< department ──< employee >── city
                                employee ──< employee_salary     (one row has is_current = TRUE)
                                employee ──< employee            (manager_id: who they report to)
```

`──<` = one-to-many. An employee's organization comes from their department;
each department has one manager, and everyone else in it reports to that manager.
`city` is where the employee works — it is not linked to an organization.

The agent has 4 tools:
- `run_sql(query)` — SELECT queries only
- `find_employee(name)` — fuzzy name search
- `disable_employee(emp_id)` — requests a disable; code asks the user, and only a "yes" reply writes
- `get_schema()` — schema lookup
