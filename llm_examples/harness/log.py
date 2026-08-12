"""Run-level progress log: mirrors every stage's progress to <run_dir>/run.log
as well as the console, so a run's full narrative survives after the process exits."""

import logging
import os


def get_logger(run_dir: str) -> logging.Logger:
    logger = logging.getLogger(f"code_harness.{os.path.basename(run_dir)}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    file_handler = logging.FileHandler(os.path.join(run_dir, "run.log"), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
