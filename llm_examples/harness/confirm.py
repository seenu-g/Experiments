"""Shared user-confirmation helper, used by DEFINE and SAVE."""


def default_confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ")
    return answer.strip().lower() == "y"
