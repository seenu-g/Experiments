"""Shared configuration for the code harness stages."""

import os

LOCAL_MODEL = "qwen2.5-coder:7b"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
MAX_STAGE_ATTEMPTS = 3
VALIDATE_TIMEOUT_SECONDS = 180
