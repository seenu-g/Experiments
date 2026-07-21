"""
Behavior evals for agent.py, run against the real local model (non-deterministic).
Unlike test_agent.py, these don't assert exact wording -- they check observable
outcomes: did the right tool get called, does the final answer contain the
expected value. Run with: python eval_agent.py
"""
import agent
from agent import SYSTEM_PROMPT, run_agent

MODELS = ["llama3.1:latest", "qwen3.5:latest"]

CASES = [
    {
        "name": "arithmetic uses calculate tool",
        "prompt": "What is 17 * 6?",
        "expected_tool": "calculate",
        "expected_in_answer": "102",
    },
    {
        "name": "time question uses get_current_time tool",
        "prompt": "What time is it right now?",
        "expected_tool": "get_current_time",
        "expected_in_answer": None,
    },
    {
        "name": "no tool needed for a plain question",
        "prompt": "What is the capital of France?",
        "expected_tool": None,
        "expected_in_answer": "Paris",
    },
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


def run_case(case):
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages = run_agent(case["prompt"], history)
    final_answer = messages[-1]["content"] if isinstance(messages[-1], dict) else messages[-1].content

    checks = []
    if case["expected_tool"]:
        ok = tool_calls_in(messages, case["expected_tool"])
        checks.append((f"called {case['expected_tool']}", ok))
    if case["expected_in_answer"]:
        ok = case["expected_in_answer"].lower() in final_answer.lower()
        checks.append((f"answer contains '{case['expected_in_answer']}'", ok))

    return checks, final_answer


def main():
    summary = {}
    for model in MODELS:
        agent.MODEL = model
        print(f"\n########## model={model} ##########")
        total, passed = 0, 0
        for case in CASES:
            print(f"\n=== {case['name']} ===")
            print(f"prompt: {case['prompt']}")
            checks, final_answer = run_case(case)
            print(f"final answer: {final_answer}")
            for label, ok in checks:
                total += 1
                passed += int(ok)
                print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        summary[model] = (passed, total)

    print("\n\n=== summary ===")
    for model, (passed, total) in summary.items():
        print(f"{model}: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()
