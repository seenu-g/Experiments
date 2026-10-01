"""
setup_db.py — Create PostgreSQL schema and seed synthetic data.

The table SQL is in schema_sql.py and the seed values in seed_data.py; this file runs them.

Run once:  python setup_db.py

Requires PostgreSQL running locally. Edit DB_CONFIG in config.py to match your setup.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from faker import Faker
import random
from datetime import date, timedelta

from config import DB_CONFIG
from schema_sql import SCHEMA
from seed_data import CITIES, DEPARTMENTS, EDUCATIONS, ORGS, SALARY_RANGES

fake = Faker()
random.seed(42)
Faker.seed(42)


def create_database():
    """Create the database named in config.DB_CONFIG if it doesn't exist."""
    db_name = DB_CONFIG["database"]
    cfg = {**DB_CONFIG, "database": "postgres"}
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        # CREATE DATABASE can't take a %s parameter; Identifier quotes the name safely
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"✓ Created database: {db_name}")
    else:
        print(f"✓ Database {db_name} already exists")
    cur.close()
    conn.close()


def seed(conn):
    cur = conn.cursor()

    # Organizations
    org_ids = []
    for name, industry, year in ORGS:
        cur.execute(
            "INSERT INTO organization(name,industry,founded_year) VALUES(%s,%s,%s) RETURNING org_id",
            (name, industry, year)
        )
        org_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(org_ids)} organizations")

    # Cities
    city_ids = []
    for name, country, tz in CITIES:
        cur.execute(
            "INSERT INTO city(name,country,timezone) VALUES(%s,%s,%s) RETURNING city_id",
            (name, country, tz)
        )
        city_ids.append(cur.fetchone()[0])
    print(f"  ✓ {len(city_ids)} cities")

    # Departments — one row per department name per org
    depts_by_org = {}                              # org_id -> [(dept_id, dept_name)]
    for org_id in org_ids:
        depts_by_org[org_id] = []
        for dept_name in DEPARTMENTS:
            cur.execute(
                "INSERT INTO department(org_id,name) VALUES(%s,%s) RETURNING dept_id",
                (org_id, dept_name)
            )
            depts_by_org[org_id].append((cur.fetchone()[0], dept_name))
    total_depts = sum(len(v) for v in depts_by_org.values())
    print(f"  ✓ {total_depts} departments")

    # Employees + salaries
    emp_count = 0
    sal_rows = []
    staff_by_dept = {}                             # dept_id -> [(emp_id, is_active)], for managers below

    for org_id in org_ids:
        depts = depts_by_org[org_id]
        n_employees = random.randint(25, 40)

        for i in range(n_employees):
            dept_id, dept_name = random.choice(depts)
            position, levels   = random.choice(DEPARTMENTS[dept_name])
            level     = random.choice(levels)
            city_id   = random.choice(city_ids)
            is_active  = random.random() > 0.1  # 10% inactive (left company)
            education  = random.choice(EDUCATIONS)
            hire_date  = fake.date_between(start_date="-8y", end_date="-3m")
            first      = fake.first_name()
            last       = fake.last_name()
            email      = f"{first.lower()}.{last.lower()}{random.randint(10,99)}@{fake.domain_name()}"

            cur.execute(
                """INSERT INTO employee
                   (dept_id,city_id,position,level,first_name,last_name,email,
                    education,hire_date,is_active)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING emp_id""",
                (dept_id, city_id, position, level, first, last, email,
                 education, hire_date, is_active)
            )
            emp_id = cur.fetchone()[0]
            emp_count += 1
            staff_by_dept.setdefault(dept_id, []).append((emp_id, is_active))

            # Salary: historical + current, the current one within the employee's level range
            lo, hi = SALARY_RANGES[level]
            current_salary = round(random.uniform(lo, hi), 2)
            eff_date = hire_date + timedelta(days=random.randint(0, 30))

            # Historical salary (lower)
            old_salary = round(current_salary * random.uniform(0.80, 0.95), 2)
            sal_rows.append((emp_id, old_salary, "USD", eff_date, False))

            # Current salary
            current_eff = eff_date + timedelta(days=random.randint(365, 730))
            sal_rows.append((emp_id, current_salary, "USD", current_eff, True))

    execute_values(
        cur,
        "INSERT INTO employee_salary(emp_id,amount,currency,effective_date,is_current) VALUES %s",
        sal_rows
    )
    print(f"  ✓ {emp_count} employees")

    # Managers: one per department, picked from its active staff; everyone else reports to them
    for dept_id, staff in staff_by_dept.items():
        active = [emp_id for emp_id, is_active in staff if is_active]
        manager = random.choice(active or [emp_id for emp_id, _ in staff])
        cur.execute("UPDATE employee SET is_manager = TRUE WHERE emp_id = %s", (manager,))
        cur.execute("UPDATE employee SET manager_id = %s WHERE dept_id = %s AND emp_id <> %s",
                    (manager, dept_id, manager))
    print(f"  ✓ {len(staff_by_dept)} managers (one per department with staff)")
    print(f"  ✓ {len(sal_rows)} salary records")

    conn.commit()
    cur.close()


def main():
    print("\n🚀 Setting up HR Agent database")
    print("─" * 40)

    create_database()

    conn = psycopg2.connect(**DB_CONFIG)
    print("\nCreating schema...")
    cur = conn.cursor()
    cur.execute(SCHEMA)
    conn.commit()
    cur.close()
    print("  ✓ Schema created")

    print("\nSeeding data...")
    seed(conn)
    conn.close()

    print(f"\n✅ Done! Database {DB_CONFIG['database']} is ready.")
    print(f"   Connect: psql -U {DB_CONFIG['user']} -d {DB_CONFIG['database']}")


if __name__ == "__main__":
    main()
