"""Shared configuration for the code harness stages."""

import os

LOCAL_MODEL = "qwen2.5-coder:7b"

# Ollama's own default (5m) unloads the model from memory/VRAM after 5 minutes of no
# requests. One full DEFINE -> PLAN -> GENERATE(source) -> GENERATE(test) -> ... iteration
# makes several separate ollama.chat() calls with a human-confirmation pause (or, on a slow
# retry loop, a long generation) between some of them -- easily longer than 5 minutes -- so
# without an explicit keep_alive, a later call in the same run can pay a full model-reload
# cost the previous call already should have avoided. "30m" keeps it resident across a
# realistic run's pauses without pinning it in memory forever (use "-1" to never unload).
OLLAMA_KEEP_ALIVE = "30m"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
MAX_STAGE_ATTEMPTS = 3
VALIDATE_TIMEOUT_SECONDS = 300

# 10s was fine for typical demo scripts (sorting, string manipulation, etc.),
# which finish near-instantly, but generated code that itself calls a local
# LLM (Ollama/LangChain tasks) can legitimately take longer than that for a
# single inference call -- especially through LangChain's OllamaLLM wrapper,
# which has enough overhead to blow past 10s even though the same prompt via
# a direct ollama.chat() call finished in ~5s. 60s gives real LLM calls
# comfortable headroom while still catching a genuine infinite loop quickly.
EXECUTE_TIMEOUT_SECONDS = 60
