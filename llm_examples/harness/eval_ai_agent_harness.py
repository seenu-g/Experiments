"""Eval for ai_agent_harness.py's DEFINE-step logic: classify_tool_types(),
describe_tool_type_matches(), and define_task() itself.

Purely about the deterministic classification -- no Ollama calls, no
execution. Sends a large batch of simulated task descriptions (varied
phrasing, casing, combinations, and descriptions that match nothing) through
classify_tool_types()/describe_tool_type_matches() to check the keyword
matching is solid, plus a few define_task() runs with input() monkeypatched
to simulate a user typing at the prompt.

Run: python eval_ai_agent_harness.py
"""

import sys
from unittest.mock import patch

# Windows' console defaults to cp1252, which can't encode emoji/non-Latin test
# input (used below to check the classifier never crashes on odd input) --
# without this, printing a check() label containing that text raises
# UnicodeEncodeError from the print() call itself, unrelated to whether
# classify_tool_types() actually handled the input fine.
sys.stdout.reconfigure(errors="replace")

from ai_agent_harness import (
    DEFAULT_TASK,
    LOCAL_MODEL,
    classify_tool_types,
    define_task,
    describe_tool_type_matches,
)

LOCAL = "local_system_call"
API = "no_auth_api"
BOTH = {LOCAL, API}


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


# (description, expected categories) -- a large, varied batch: different phrasings,
# casing, combinations, and descriptions that should fall back to both categories.
CLASSIFY_CASES = [
    # --- local_system_call only, varied phrasing ---
    ("Write a tool that gets the current date and time.", {LOCAL}),
    ("What time is it right now?", {LOCAL}),
    ("Tell me the date.", {LOCAL}),
    ("Get system info about this laptop.", {LOCAL}),
    ("How much memory does this machine have?", {LOCAL}),
    ("Report the CPU and disk usage.", {LOCAL}),
    ("List the running processes on this computer.", {LOCAL}),
    ("Show me all processes currently running.", {LOCAL}),
    ("GET THE CURRENT DATE AND TIME", {LOCAL}),  # all caps
    ("dAtE and TiMe please", {LOCAL}),  # mixed case
    ("What's my laptop's CPU count?", {LOCAL}),
    # --- no_auth_api only, varied phrasing ---
    ("Perform a web search for the latest news.", {API}),
    ("Search the web for Python tutorials.", {API}),
    ("Do an internet search about black holes.", {API}),
    ("WEB SEARCH for cat videos", {API}),  # all caps
    # --- both categories present ---
    (
        "Write a program that uses a local LLM with tool-calling to answer questions "
        "using four tools: getting the current date/time, performing a web search, "
        "getting system info of the laptop it runs on, and getting the list of currently "
        "running processes. Demonstrate the agent using at least one question that should "
        "route to each of the four tools.",
        BOTH,
    ),
    (DEFAULT_TASK, BOTH),
    ("Get the time, then do a web search for related news.", BOTH),
    ("Search the web, then tell me the current date and how much memory is free.", BOTH),
    # --- neither matches -> falls back to both (opt-in behavior, not silent no-op) ---
    ("Write a function that reverses a string.", BOTH),
    ("Build a calculator that adds two numbers.", BOTH),
    ("", BOTH),
    ("   ", BOTH),
    ("asdkjhaskjdh random gibberish text", BOTH),
]


def eval_classify_tool_types_batch():
    ok = True
    for description, expected in CLASSIFY_CASES:
        got = classify_tool_types(description)
        ok &= check(
            f"classify_tool_types({description[:50]!r}...)" if len(description) > 50 else f"classify_tool_types({description!r})",
            got == expected,
            f"expected {expected}, got {got}",
        )
    return ok


def eval_classify_tool_types_is_case_insensitive():
    ok = True
    ok &= check(
        "lowercase 'web search' matches",
        classify_tool_types("web search for x") == {API},
    )
    ok &= check(
        "uppercase 'WEB SEARCH' matches identically",
        classify_tool_types("WEB SEARCH for x") == {API},
    )
    ok &= check(
        "mixed-case 'WeB sEaRcH' matches identically",
        classify_tool_types("WeB sEaRcH for x") == {API},
    )
    return ok


def eval_classify_tool_types_never_raises_on_odd_input():
    """Robustness: no description should ever crash the classifier, regardless
    of length, unicode content, or type of gibberish."""
    odd_inputs = [
        "a" * 5000,
        "🕐🔍💻 emoji only",
        "日付と時刻を取得する",  # non-English text
        "\n\n\t\t   ",
        "date" * 200,  # pathological repetition
    ]
    ok = True
    for text in odd_inputs:
        try:
            result = classify_tool_types(text)
            ok &= check(f"no crash on odd input ({text[:20]!r}...)", isinstance(result, set))
        except Exception as e:
            ok &= check(f"no crash on odd input ({text[:20]!r}...)", False, f"raised {e!r}")
    return ok


def eval_describe_tool_type_matches_returns_matched_text():
    ok = True
    matches = describe_tool_type_matches("Get the current date and time, then do a web search.")
    categories = {category for _, category in matches}
    ok &= check(
        "describe_tool_type_matches finds both categories in a mixed description",
        categories == BOTH,
        matches,
    )
    ok &= check(
        "describe_tool_type_matches includes the literal matched substrings",
        any(text.lower() == "date" for text, _ in matches) and any(text.lower() == "web search" for text, _ in matches),
        matches,
    )

    no_match = describe_tool_type_matches("Sort a list of numbers.")
    ok &= check(
        "describe_tool_type_matches returns empty list when nothing matches",
        no_match == [],
        no_match,
    )
    return ok


def eval_define_task_blank_input_uses_default():
    with patch("builtins.input", return_value=""):
        result = define_task()
    return check("define_task() with blank input returns DEFAULT_TASK", result == DEFAULT_TASK)


def eval_define_task_returns_typed_description_unchanged():
    typed = "Search the web for today's weather."
    with patch("builtins.input", return_value=typed):
        result = define_task()
    return check("define_task() returns the user's typed description verbatim", result == typed)


def eval_define_task_never_raises_across_many_simulated_prompts():
    """Simulate a batch of different users typing at the prompt -- define_task()
    must never crash and must always return exactly what was typed (or the
    default on blank), regardless of phrasing."""
    simulated_prompts = [d for d, _ in CLASSIFY_CASES if d.strip()] + [
        "Just get me the date, nothing else.",
        "I need CPU, memory, disk, AND a web search all in one.",
        "¿Cuál es la hora actual?",  # non-English
        "SEARCH THE WEB!!! for something!!!",
    ]
    ok = True
    for prompt in simulated_prompts:
        try:
            with patch("builtins.input", return_value=prompt):
                result = define_task()
            ok &= check(
                f"define_task() handles {prompt[:40]!r}... without crashing",
                result == prompt,
                f"returned {result!r}",
            )
        except Exception as e:
            ok &= check(f"define_task() handles {prompt[:40]!r}...", False, f"raised {e!r}")
    return ok


def eval_define_task_mentions_llm_and_model_name():
    """Manual stdout capture (not pytest's capsys) so this file stays runnable standalone."""
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf), patch("builtins.input", return_value=""):
        define_task()
    output = buf.getvalue()

    ok = True
    ok &= check(
        "define_task() output explicitly mentions an LLM is required",
        "LLM" in output,
        output,
    )
    ok &= check(
        "define_task() output explicitly names the model being used",
        LOCAL_MODEL in output,
        output,
    )
    return ok


if __name__ == "__main__":
    results = [
        eval_classify_tool_types_batch(),
        eval_classify_tool_types_is_case_insensitive(),
        eval_classify_tool_types_never_raises_on_odd_input(),
        eval_describe_tool_type_matches_returns_matched_text(),
        eval_define_task_blank_input_uses_default(),
        eval_define_task_returns_typed_description_unchanged(),
        eval_define_task_never_raises_across_many_simulated_prompts(),
        eval_define_task_mentions_llm_and_model_name(),
    ]

    total = len(CLASSIFY_CASES) + len(results)
    passed = sum(1 for r in results if r)
    print(f"\n{passed}/{len(results)} eval functions passed (covering {len(CLASSIFY_CASES)} classify cases + define_task checks).")
    sys.exit(0 if all(results) else 1)
