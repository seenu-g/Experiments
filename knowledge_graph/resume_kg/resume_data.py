"""
Shared loader for resume data used by kg_employer*/kg_education*. Reads the
structured resume (person, employers, roles, institutions, degrees) from a
JSON file instead of hardcoding it per script — swap RESUME_PATH (or pass a
path explicitly) to run these graphs against a different resume once an
extractor produces the same JSON shape as fixtures/srinivasan_resume.json.
"""
import json
import os
import shutil

RESUME_PATH = "fixtures/srinivasan_resume.json"
OUTPUT_ROOT = "output"


def load_resume(path: str = RESUME_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def person_output_dir(person: str, resume_path: str = RESUME_PATH) -> str:
    """output/<person>/ — created if missing, with a copy of the source resume.json."""
    slug = person.strip().replace(" ", "_")
    out_dir = os.path.join(OUTPUT_ROOT, slug)
    os.makedirs(out_dir, exist_ok=True)
    shutil.copy(resume_path, os.path.join(out_dir, "resume.json"))
    return out_dir
