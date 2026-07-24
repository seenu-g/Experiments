"""
Regression check against the one resume we've manually verified end to end
(fixtures/srinivasan_resume.json). Run this after any change to extraction
logic or to the ROLE_HEADERS/DEGREE_HEADERS constants in the kg*.py files —
it's the one case where we know the correct answer, so it should never
silently drift.

No pytest dependency; run directly with `python test_golden_resume.py`.
"""
import json

import kg_employer as emp_kg
import kg_education as edu_kg

FIXTURE_PATH = "fixtures/srinivasan_resume.json"


def load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def check(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label} mismatch.\n  expected: {expected}\n  actual:   {actual}")
    print(f"  OK  {label}")


def main():
    fixture = load_fixture()

    employers = emp_kg.build_employers()
    roles = emp_kg.build_roles(employers)
    check("person", emp_kg.PERSON, fixture["person"])
    check("employers", employers, fixture["employers"])
    check("roles", roles, fixture["roles"])

    institutions = edu_kg.build_institutions()
    degrees = edu_kg.build_education(institutions)
    check("institutions", institutions, fixture["institutions"])
    check("degrees", degrees, fixture["degrees"])

    print("All checks passed against golden fixture.")


if __name__ == "__main__":
    main()
