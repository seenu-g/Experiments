"""
seed_data.py — Synthetic values setup_db.py inserts: organizations, cities,
departments with their positions and levels, educations and salary ranges.

If you change counts or ranges here, update EXPECTED_ROWS / SALARY_RANGES in eval_expected.py.
"""

ORGS = [
    ("Apex Fintech Ltd",       "Financial Technology", 2012),
    ("BrightLearn Edtech",     "Education Technology", 2015),
    ("CoreSoft Solutions",     "Enterprise Software",  2008),
]

CITIES = [
    ("New York",   "USA",    "America/New_York"),
    ("London",     "UK",     "Europe/London"),
    ("Bengaluru",  "India",  "Asia/Kolkata"),
    ("Singapore",  "SG",     "Asia/Singapore"),
    ("Berlin",     "Germany","Europe/Berlin"),
]

# Department -> positions in it, each with the levels that position can have.
# One department row per name per org; each employee gets their own position and level.
DEPARTMENTS = {
    "Engineering":     [("Software Engineer", ["Junior", "Senior", "Lead"]),
                        ("DevOps Engineer",   ["Junior", "Senior"])],
    "Product":         [("Product Manager",   ["Associate", "Senior", "Principal"])],
    "Data":            [("Data Analyst",      ["Junior", "Senior"]),
                        ("Data Scientist",    ["Senior", "Lead"])],
    "Finance":         [("Financial Analyst", ["Junior", "Senior"])],
    "Human Resources": [("HR Specialist",     ["Junior", "Senior"])],
    "Sales":           [("Account Executive", ["Junior", "Senior", "Lead"])],
}

EDUCATIONS = [
    "BSc Computer Science", "MSc Computer Science", "BSc Information Technology",
    "MBA", "BSc Finance", "MSc Data Science", "BSc Mathematics",
    "MSc Software Engineering", "PhD Computer Science", "BSc Business Administration",
    "MSc Finance", "BSc Electrical Engineering",
]

SALARY_RANGES = {
    "Junior":    (55_000,  85_000),
    "Associate": (65_000,  95_000),
    "Senior":    (90_000, 140_000),
    "Lead":      (130_000, 180_000),
    "Principal": (160_000, 220_000),
}
