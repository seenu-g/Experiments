"""Delete a fixed list of local Ollama models via `ollama rm`.

Models here were identified as unused by grepping the Ollama server logs
(%LOCALAPPDATA%\\Ollama\\server*.log) for "using llama-server for model" lines
and finding which pulled models never appeared -- see MODELS_TO_DELETE below.
Edit the list before re-running for a different cleanup pass.
"""

import subprocess
import sys

MODELS_TO_DELETE = [
    "gaganyatri/sarvam-2b-v0.5:latest",
    "codegemma:latest",
    "gemma2:2b",
    "ZimaBlueAI/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF:latest",
    "deepseek-r1:8b",
    "qwen3.5:latest",
    "qwen2.5-coder:3b",
    "phi4-mini:latest",
]


def delete_models(model_names: list[str]) -> None:
    for name in model_names:
        result = subprocess.run(
            ["ollama", "rm", name], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"deleted: {name}")
        else:
            print(f"failed to delete {name}: {result.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    delete_models(MODELS_TO_DELETE)
