"""Shared user-confirmation helper, used by DEFINE, PLAN, and SAVE."""


def default_confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ")
    return answer.strip().lower() == "y"


def auto_confirm(prompt: str) -> bool:
    """Always accepts, without waiting for real input -- the default confirm() for
    code_harness.py's __main__ entrypoint (pass --interactive on the command line to get
    real y/N prompts back via default_confirm instead).

    Why: DEFINE, PLAN, and SAVE-permission each call confirm() once per version, and every
    ollama.chat() call has an explicit keep_alive set (see config.OLLAMA_KEEP_ALIVE), but a
    human reading and confirming a restated spec or a multi-file plan can still easily run
    long -- and every extra minute waiting on a person is a minute the harness spends idle
    for no benefit once the confirm loop itself is understood well enough not to need
    watching every time. The confirmed spec/plan TEXT is still written to run.log either
    way (see define.define_task/plan.plan_task, which log it before ever calling confirm())
    -- only the wait is skipped, nothing about what was confirmed is lost."""
    print(f"{prompt} [auto-confirmed, non-interactive mode]")
    return True
