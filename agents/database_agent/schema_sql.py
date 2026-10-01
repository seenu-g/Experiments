"""
schema_sql.py — SQL that creates the HR tables (run by setup_db.py).

Not the same as db_schema.py: that one is the short description the model is told.
If you change a table here, update db_schema.py and eval_expected.py to match.
"""

SCHEMA = """
DROP TABLE IF EXISTS employee_salary CASCADE;
DROP TABLE IF EXISTS employee       CASCADE;
DROP TABLE IF EXISTS department     CASCADE;
DROP TABLE IF EXISTS city           CASCADE;
DROP TABLE IF EXISTS organization   CASCADE;

CREATE TABLE organization (
    org_id       SERIAL PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    industry     VARCHAR(80),
    founded_year INT
);

CREATE TABLE city (
    city_id  SERIAL PRIMARY KEY,
    name     VARCHAR(80) NOT NULL,
    country  VARCHAR(80) NOT NULL,
    timezone VARCHAR(50)
);

-- One row per real department; job role (position/level) belongs to the employee.
CREATE TABLE department (
    dept_id  SERIAL PRIMARY KEY,
    org_id   INT NOT NULL REFERENCES organization(org_id),
    name     VARCHAR(80) NOT NULL,
    UNIQUE (org_id, name)
);

-- Organization comes from the department (no org_id here, so the two can never disagree).
-- manager_id: who this employee reports to; NULL for department managers.
CREATE TABLE employee (
    emp_id      SERIAL PRIMARY KEY,
    dept_id     INT NOT NULL REFERENCES department(dept_id),
    manager_id  INT REFERENCES employee(emp_id),
    city_id     INT NOT NULL REFERENCES city(city_id),
    position    VARCHAR(80) NOT NULL,   -- e.g. 'Software Engineer', 'Data Analyst'
    level       VARCHAR(30) NOT NULL
                CHECK (level IN ('Junior', 'Associate', 'Senior', 'Lead', 'Principal')),
    first_name  VARCHAR(60) NOT NULL,
    last_name   VARCHAR(60) NOT NULL,
    email       VARCHAR(120) UNIQUE NOT NULL,
    is_manager  BOOLEAN DEFAULT FALSE,
    education   VARCHAR(80),        -- 'BSc Computer Science', 'MBA', etc.
    hire_date   DATE,
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE TABLE employee_salary (
    sal_id         SERIAL PRIMARY KEY,
    emp_id         INT NOT NULL REFERENCES employee(emp_id),
    amount         NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency       CHAR(3) DEFAULT 'USD',
    effective_date DATE NOT NULL,
    is_current     BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_emp_dept    ON employee(dept_id);
CREATE INDEX idx_emp_active  ON employee(is_active);
CREATE INDEX idx_emp_manager ON employee(is_manager);
CREATE INDEX idx_emp_reports ON employee(manager_id);
CREATE INDEX idx_sal_emp     ON employee_salary(emp_id);
CREATE INDEX idx_sal_current ON employee_salary(is_current);

-- The database itself enforces "one current salary per employee".
CREATE UNIQUE INDEX uq_sal_one_current ON employee_salary(emp_id) WHERE is_current;
"""
