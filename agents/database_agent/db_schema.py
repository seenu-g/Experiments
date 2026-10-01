"""
db_schema.py — What the model is told about the HR database.

Sent to the model on every call (inside the instructions), so every line here costs
tokens on every call. Example queries are tested against the real database.
"""

DB_SCHEMA = """
Tables:
  organization  (org_id PK, name, industry, founded_year)
  city          (city_id PK, name, country, timezone)
  department    (dept_id PK, org_id FK, name)   -- one row per department per org
  employee      (emp_id PK, dept_id FK, city_id FK,
                 manager_id FK -> employee.emp_id,  -- who they report to; NULL for managers
                 position, level,               -- level: Junior|Associate|Senior|Lead|Principal
                 first_name, last_name, email,
                 is_manager BOOL, education, hire_date, is_active BOOL)
  employee_salary (sal_id PK, emp_id FK, amount, currency,
                   effective_date, is_current BOOL)

Key rules:
  - Always filter is_active = TRUE unless the user asks about inactive/disabled employees.
  - Current salary: JOIN employee_salary WHERE is_current = TRUE.
  - Managers: WHERE is_manager = TRUE (one per department).
  - Reports of a manager: WHERE e.manager_id = <manager emp_id>. An employee's manager:
    LEFT JOIN employee m ON m.emp_id = e.manager_id - LEFT, because managers have
    manager_id = NULL and a plain JOIN silently drops them (manager shows as NULL = reports to nobody).
  - Organization of an employee: JOIN department d ON d.dept_id = e.dept_id, then d.org_id.
  - Full name: first_name || ' ' || last_name.
  - Job role and seniority are on employee (position, level), not on department.
  - Department names repeat across orgs: include organization when grouping by department.
  - To disable an employee use the disable_employee tool — never write raw UPDATE.
  - Never hard-code ids (dept_id, emp_id, org_id) from earlier answers: filter by name through joins,
    e.g. JOIN department d ... WHERE d.name = 'Data'.

Example queries (tested; copy their joins):
  -- All managers with department and organization
  SELECT e.first_name || ' ' || e.last_name AS manager, d.name AS department, o.name AS organization
  FROM employee e
  JOIN department d ON d.dept_id = e.dept_id
  JOIN organization o ON o.org_id = d.org_id
  WHERE e.is_manager = TRUE AND e.is_active = TRUE
  ORDER BY o.name, d.name;

  -- One employee's position and manager (LEFT JOIN: a manager has no manager, manager = NULL)
  SELECT e.first_name || ' ' || e.last_name AS employee, e.position, e.level, e.is_manager,
         m.first_name || ' ' || m.last_name AS manager
  FROM employee e
  LEFT JOIN employee m ON m.emp_id = e.manager_id
  WHERE e.first_name = 'Michael' AND e.last_name = 'Osborn';

  -- Everyone who reports to a manager (plain JOIN is right here: only people WITH a manager)
  -- (alias e = employee, m = their manager; both are the employee table)
  SELECT e.first_name || ' ' || e.last_name AS employee, e.position,
         m.first_name || ' ' || m.last_name AS manager
  FROM employee e
  JOIN employee m ON m.emp_id = e.manager_id
  JOIN department d ON d.dept_id = e.dept_id
  JOIN organization o ON o.org_id = d.org_id
  WHERE d.name = 'Engineering' AND o.name = 'Apex Fintech Ltd' AND e.is_active = TRUE;
"""
