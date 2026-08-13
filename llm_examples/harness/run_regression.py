"""Runs the persisted regression corpus (input/regression_corpus.json) against the
real harness, sequentially (never in parallel -- concurrent code_harness.py processes
have caused real Ollama/GPU contention crashes), and writes REGRESSION_RESULTS.md.

Each sample is run exactly as a real user would invoke it: piped into a fresh
`python -c "from code_harness import run_harness; run_harness(is_test=True)"`
process via stdin (description, then 'y' to confirm the spec, then 'y' to grant
save permission). is_test=True so these land in input/test_prompts.txt, not
input/user_prompts.txt, same convention as every other scripted run.

REGRESSION_RESULTS.md is meant to be committed after each run -- an ordinary git
diff against the previous commit is the actual point: it makes "did the last
harness change (or a config.LOCAL_MODEL swap) make things better or worse"
visible at a glance, instead of re-discovering the same edge cases from scratch.

Run: python run_regression.py
"""

import json
import os
import re
import subprocess
import sys
import time

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HARNESS_DIR, "input", "regression_corpus.json")
OUTPUT_DIR = os.path.join(HARNESS_DIR, "output")
RESULTS_PATH = os.path.join(HARNESS_DIR, "REGRESSION_RESULTS.md")

RUN_HARNESS_CODE = "from code_harness import run_harness; run_harness(is_test=True)"
PER_SAMPLE_TIMEOUT_SECONDS = 1800  # 30 min -- generous, source+test rounds can retry up to 3x each


def _existing_run_dirs() -> set:
    if not os.path.isdir(OUTPUT_DIR):
        return set()
    return {d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))}


def _new_run_dir(before: set) -> str | None:
    """The one run_id directory that appeared under output/ during this sample's
    invocation -- reliable because samples run strictly sequentially."""
    after = _existing_run_dirs()
    new_dirs = after - before
    if not new_dirs:
        return None
    return sorted(new_dirs)[-1]


def _parse_result(run_log_text: str) -> tuple[str, str]:
    """Returns (result, version_detail) by pattern-matching run.log's own
    conclusion lines -- code_harness.py already logs exactly one of these three
    outcomes at the end of run_harness()."""
    success = re.search(r"SUCCESS on v(\d+)", run_log_text)
    if success:
        return "PASS", f"v{success.group(1)}"

    failed = re.search(r"FAILED: no attempt succeeded within (\d+) versions", run_log_text)
    if failed:
        return "FAIL", f"all {failed.group(1)} exhausted"

    if "Stopping run" in run_log_text:
        return "STOPPED", "environment issue (VALIDATE)"

    return "UNKNOWN", "run did not reach a conclusion"


def run_sample(sample: dict) -> dict:
    description = sample["description"]
    stdin_input = f"{description}\ny\ny\n"

    print(f"=== Running: {sample['id']} ===")
    before = _existing_run_dirs()
    try:
        subprocess.run(
            [sys.executable, "-c", RUN_HARNESS_CODE],
            input=stdin_input,
            capture_output=True,
            text=True,
            cwd=HARNESS_DIR,
            timeout=PER_SAMPLE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        run_id = _new_run_dir(before)
        return {**sample, "result": "TIMEOUT", "detail": f"exceeded {PER_SAMPLE_TIMEOUT_SECONDS}s", "run_id": run_id or "unknown"}

    run_id = _new_run_dir(before)
    if run_id is None:
        return {**sample, "result": "UNKNOWN", "detail": "no output/<run_id> directory was created", "run_id": "unknown"}

    run_log_path = os.path.join(OUTPUT_DIR, run_id, "run.log")
    if not os.path.exists(run_log_path):
        return {**sample, "result": "UNKNOWN", "detail": "run.log was never written", "run_id": run_id}

    with open(run_log_path, encoding="utf-8") as f:
        run_log_text = f.read()

    result, detail = _parse_result(run_log_text)
    return {**sample, "result": result, "detail": detail, "run_id": run_id}


def _format_table(samples: list[dict]) -> str:
    lines = ["| Sample | Result | Version | Run |", "|---|---|---|---|"]
    for s in samples:
        lines.append(f"| {s['id']} | {s['result']} | {s['detail']} | {s['run_id']} |")
    return "\n".join(lines)


def write_results(results: list[dict]) -> None:
    deterministic = [r for r in results if r["verification"] == "deterministic"]
    probabilistic = [r for r in results if r["verification"] == "probabilistic"]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    content = (
        f"# Regression Results\n\n"
        f"Generated {timestamp} by `run_regression.py` against `config.LOCAL_MODEL`.\n"
        f"Commit this file after each run -- the git diff against the previous run "
        f"is the point.\n\n"
        f"## Deterministic ({len(deterministic)})\n\n"
        f"{_format_table(deterministic)}\n\n"
        f"## Probabilistic ({len(probabilistic)}) -- a FAIL here may just be model "
        f"variance (the response text is never exactly reproducible); spot-check the "
        f"linked run.log before treating it as a regression\n\n"
        f"{_format_table(probabilistic)}\n"
    )
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nWrote {RESULTS_PATH}")


def main():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        corpus = json.load(f)

    results = [run_sample(sample) for sample in corpus]
    write_results(results)

    passed = sum(1 for r in results if r["result"] == "PASS")
    print(f"\n{passed}/{len(results)} samples PASSED.")


if __name__ == "__main__":
    main()
