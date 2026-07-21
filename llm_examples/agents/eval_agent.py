"""
Behavior evals for agent.py, run against the real local model (non-deterministic).
Unlike test_agent.py, these don't assert exact wording -- they check observable
outcomes: did the right tool get called, does the final answer contain the
expected value. Run with: python eval_agent.py
"""
import tempfile
from datetime import datetime
from pathlib import Path

import ollama

import agent
from agent import SYSTEM_PROMPT, run_agent

MODELS = ["llama3.1:latest", "qwen3.5:latest"]


def _auto_approve(name, args):
    return True


# Each entry is a factory (not a static dict) because read_file/delete_file
# need a fresh real file created right before the case runs -- especially
# delete_file, which consumes the file each time it's exercised.

def case_arithmetic():
    return {
        "name": "arithmetic uses calculate tool",
        "prompt": "What is 17 * 6?",
        "expected_tool": "calculate",
        "expected_in_answer": "102",
    }


def _time_is_grounded(tool_result, final_answer):
    # tool_result is the literal string get_current_time() returned, e.g.
    # "2026-07-21 23:55:09" -- can't hardcode this since it changes every run,
    # so instead check the answer reflects the *actual* value from the tool
    # (year + day), not something the model made up from training knowledge.
    parsed = datetime.strptime(tool_result, "%Y-%m-%d %H:%M:%S")
    return str(parsed.year) in final_answer and str(parsed.day) in final_answer


def case_current_time():
    return {
        "name": "time question uses get_current_time tool and reports its actual result",
        "prompt": "What time is it right now?",
        "expected_tool": "get_current_time",
        "expected_in_answer": None,
        "ground_check": _time_is_grounded,
    }


def case_no_tool_needed():
    return {
        "name": "no tool needed for a plain question",
        "prompt": "What is the capital of France?",
        "expected_tool": None,
        "expected_in_answer": "Paris",
    }


def case_read_file():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    f.write("the secret code is banana77")
    f.close()
    return {
        "name": "read_file reads and reports real file contents",
        "prompt": f"Read the file at {f.name} and tell me exactly what it says.",
        "expected_tool": "read_file",
        "expected_in_answer": "banana77",
    }


def case_delete_file_approved():
    f = tempfile.NamedTemporaryFile(delete=False)
    path = f.name
    f.close()
    return {
        "name": "delete_file deletes a real file when approved",
        "prompt": f"Please delete the file at {path}.",
        "expected_tool": "delete_file",
        "expected_in_answer": None,
        "confirm": _auto_approve,
        "post_check": lambda: (
            not Path(path).exists(),
            f"expected {path} to be deleted but it still exists",
        ),
    }


CASE_FACTORIES = [
    case_arithmetic,
    case_current_time,
    case_no_tool_needed,
    case_read_file,
    case_delete_file_approved,
]


def tool_calls_in(messages, tool_name):
    for m in messages:
        calls = m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)
        if not calls:
            continue
        for c in calls:
            if c["function"]["name"] == tool_name:
                return True
    return False


def find_tool_result(messages, tool_name):
    """Return the raw string a given tool call actually returned, or None if it
    wasn't called. Matches call position to result position since the loop
    appends tool-role messages in the same order as the tool_calls list."""
    for i, m in enumerate(messages):
        calls = m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)
        if not calls:
            continue
        for j, c in enumerate(calls):
            if c["function"]["name"] == tool_name:
                tool_msgs = [mm for mm in messages[i + 1:] if isinstance(mm, dict) and mm.get("role") == "tool"]
                if j < len(tool_msgs):
                    return tool_msgs[j]["content"]
    return None


def run_case(case):
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    confirm = case.get("confirm", agent._default_confirm)
    messages = run_agent(case["prompt"], history, confirm=confirm)
    final_answer = messages[-1]["content"] if isinstance(messages[-1], dict) else messages[-1].content

    checks = []
    if case["expected_tool"]:
        ok = tool_calls_in(messages, case["expected_tool"])
        checks.append((f"called {case['expected_tool']}", ok))
    if case["expected_in_answer"]:
        ok = case["expected_in_answer"].lower() in final_answer.lower()
        checks.append((f"answer contains '{case['expected_in_answer']}'", ok))
    if "ground_check" in case:
        tool_result = find_tool_result(messages, case["expected_tool"])
        ok = tool_result is not None and case["ground_check"](tool_result, final_answer)
        checks.append((f"answer reflects tool's actual return value ({tool_result!r})", ok))
    if "post_check" in case:
        ok, label = case["post_check"]()
        checks.append((label, ok))

    return checks, final_answer


def unload_model(model):
    # keep_alive=0 tells Ollama to drop this model from memory right away,
    # instead of waiting out its default keep-alive window -- otherwise the
    # next model in MODELS would load in while this one is still resident.
    ollama.generate(model=model, keep_alive=0)


def main():
    summary = {}
    for i, model in enumerate(MODELS):
        agent.MODEL = model
        print(f"\n########## model={model} ##########")
        total, passed = 0, 0
        for factory in CASE_FACTORIES:
            case = factory()
            print(f"\n=== {case['name']} ===")
            print(f"prompt: {case['prompt']}")
            checks, final_answer = run_case(case)
            print(f"final answer: {final_answer}")
            for label, ok in checks:
                total += 1
                passed += int(ok)
                print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        summary[model] = (passed, total)

        if i < len(MODELS) - 1:
            print(f"\n[unloading {model} before loading next model]")
            unload_model(model)

    print("\n\n=== summary ===")
    for model, (passed, total) in summary.items():
        print(f"{model}: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()
