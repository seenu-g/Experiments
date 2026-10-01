"""
eval_expected.py — What eval_setup_db.py expects the hr_agent database to look like.

Written out here on purpose, not read from schema_sql.SCHEMA: if a CREATE TABLE
were deleted there, the eval must still catch it.
"""

EXPECTED_COLUMNS = {
    "organization":    ["org_id", "name", "industry", "founded_year"],
    "city":            ["city_id", "name", "country", "timezone"],
    "department":      ["dept_id", "org_id", "name"],
    "employee":        ["emp_id", "dept_id", "manager_id", "city_id", "position", "level", "first_name",
                        "last_name", "email", "is_manager", "education", "hire_date", "is_active"],
    "employee_salary": ["sal_id", "emp_id", "amount", "currency", "effective_date", "is_current"],
}

# Columns that must NOT exist any more (removed as redundant).
REMOVED_COLUMNS = {("employee", "org_id")}     # organization comes from the department

EXPECTED_INDEXES = {"idx_emp_dept", "idx_emp_active", "idx_emp_manager", "idx_emp_reports",
                    "idx_sal_emp", "idx_sal_current", "uq_sal_one_current"}

# (table, column) -> referenced table
EXPECTED_FKS = {
    ("department", "org_id"): "organization",
    ("employee", "dept_id"): "department",
    ("employee", "manager_id"): "employee",
    ("employee", "city_id"): "city",
    ("employee_salary", "emp_id"): "employee",
}

# Foreign keys allowed to be NULL: department managers report to nobody.
NULLABLE_FKS = {("employee", "manager_id")}

# Same ranges as seed_data.SALARY_RANGES - repeated on purpose, see note above.
SALARY_RANGES = {"Junior": (55_000, 85_000), "Associate": (65_000, 95_000), "Senior": (90_000, 140_000),
                 "Lead": (130_000, 180_000), "Principal": (160_000, 220_000)}

# From the seed data: 3 orgs, 5 cities, 6 departments per org, 25-40 employees per org.
EXPECTED_ROWS = {
    "organization": (3, 3),
    "city": (5, 5),
    "department": (18, 18),
    "employee": (75, 120),
}
