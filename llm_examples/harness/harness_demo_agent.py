import os
import re
import subprocess
import sys
import time
import numpy as np
import ollama

# =====================================================================
# GLOBAL CONFIGURATION (Switch models here; changes apply on restart)
# =====================================================================
LOCAL_MODEL = "qwen2.5-coder:7b"
# LOCAL_MODEL = "deepseek-r1:8b"  # Reasoning alternative for complex bugs

EMBED_MODEL = "nomic-embed-text:latest"
SANDBOX_FILE = f"harness_sandbox_{time.strftime('%Y%m%d_%H%M%S')}.py"

# =====================================================================
# PART 1: LEARNING LOCAL EMBEDDINGS & RETRIEVAL (RAG)
# =====================================================================
# This mock knowledge base simulates your local codebase or documentation files.
KNOWLEDGE_BASE = [
    "def calculate_factorial(n): Return math.factorial(n). Requires importing math.",
    "def validate_email(email): Checks if string has exactly one '@' and ends with '.com'.",
    "def safe_divide(a, b): Returns a / b but handles ZeroDivisionError by returning 0."
]

def get_local_embedding(text: str) -> list:
    """Generates a numerical vector representation of text using your local embedding model."""
    try:
        response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"⚠️ Embedding failed. Ensure {EMBED_MODEL} is pulled. Error: {e}")
        return []

def retrieve_relevant_context(user_query: str, top_k: int = 1) -> str:
    """Compares the user query vector against your codebase vectors to find matching logic."""
    print(f"🔍 Vector Search: Indexing codebase context using {EMBED_MODEL}...")
    
    query_vector = get_local_embedding(user_query)
    if not query_vector:
        return ""
        
    best_match = ""
    highest_similarity = -1.0
    
    for doc in KNOWLEDGE_BASE:
        doc_vector = get_local_embedding(doc)
        if not doc_vector:
            continue
            
        # Cosine similarity calculation to find closest semantic match
        similarity = np.dot(query_vector, doc_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(doc_vector))
        
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = doc
            
    print(f"✨ Retrieved best reference context (Similarity: {highest_similarity:.2f})")
    return best_match

# =====================================================================
# PART 2: LLM COMMUNICATOR & HARNESS LOOPS
# =====================================================================
def ask_local_model_for_code(prompt: str, reference_context: str = "", error_context: str = "", interactive: bool = False) -> str:
    """Queries the user-selected model with system instructions, context, and error feedback."""

    system_instruction = (
        "You are an expert Python software engineer. Your task is to output ONLY valid, "
        "executable Python code, with no conversational preamble, explanations, or commentary. "
        "Every 'import' statement required by any function, class, or standard-library call you use "
        "must be included at the top of its file. Never reference a module or name without importing it first.\n\n"
        "If the task can be done in a single file, output exactly one ```python ... ``` block.\n\n"
        "If the task explicitly requires multiple files (e.g. one module imported by another), output "
        "one ```python ... ``` block per file, and immediately BEFORE each block put a line in exactly "
        "this form:\n"
        "# === FILE: <filename.py> ===\n"
        "All files you output will be saved together in the same folder, so a plain "
        "'import <filename_without_.py>' between them will resolve correctly. Put the file that should "
        "be run directly (the one with 'if __name__ == \"__main__\":') LAST, and mark the line right "
        "after its FILE header with:\n"
        "# === ENTRYPOINT ===\n"
        "Do not use this multi-file format unless the task genuinely requires more than one file."
    )

    if interactive:
        system_instruction += (
            "\n\nThis script WILL be run attached to a real terminal, so it is safe to use "
            "'input()' to prompt the user for values if that fits the task."
        )
    else:
        system_instruction += (
            "\n\nThis script will be run non-interactively with no terminal attached. "
            "Never call 'input()' or otherwise wait on interactive/stdin input. If the task implies "
            "user-provided values, demonstrate the function with hardcoded example arguments under "
            "'if __name__ == \"__main__\":' instead."
        )

    # If the vector search found relevant files, inject them here
    if reference_context:
        system_instruction += f"\n\nUse this local code context as a structural reference:\n{reference_context}"
        
    # If a previous execution step failed, append the raw compiler logs
    if error_context:
        # Special optimization for deepseek-r1 reasoning chains
        if "deepseek-r1" in LOCAL_MODEL:
            system_instruction += "\nThink step-by-step to identify the bug before generating the fixed script."
        system_instruction += f"\n\nCRITICAL: Your previous code failed execution. Completely fix this traceback:\n{error_context}"
        
    print(f"🤖 Querying Active Model: [{LOCAL_MODEL}]")
    
    response = ollama.chat(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.1} # Keeps output strict and code-focused
    )
    return response['message']['content']

FILE_BLOCK_RE = re.compile(
    r"#\s*===\s*FILE:\s*(?P<fname>\S+\.py)\s*===\s*"
    r"(?P<entry>#\s*===\s*ENTRYPOINT\s*===\s*)?"
    r"```python\s*(?P<code>.*?)\s*```",
    re.DOTALL,
)

def parse_and_write_files(raw_llm_text: str, target_dir: str, default_filename: str) -> tuple[list, str]:
    """Extracts one or more named code files from the model's reply and saves them to target_dir.

    Supports two model output shapes:
    - Single unlabeled ```python block: written out as default_filename (legacy/simple case).
    - One or more '# === FILE: name.py ===' + ```python blocks (optionally multi-file, with one
      block flagged '# === ENTRYPOINT ===' as the file to execute).

    Returns (list_of_written_paths, entry_file_path).
    """
    clean_text = re.sub(r"<think>.*?</think>", "", raw_llm_text, flags=re.DOTALL)
    os.makedirs(target_dir, exist_ok=True)

    matches = list(FILE_BLOCK_RE.finditer(clean_text))

    if not matches:
        code_match = re.search(r"```python\s*(.*?)\s*```", clean_text, re.DOTALL)
        clean_code = code_match.group(1).strip() if code_match else clean_text.strip()
        path = os.path.join(target_dir, default_filename)
        with open(path, "w") as file:
            file.write(clean_code)
        return [path], path

    written_paths = []
    entry_path = None
    for match in matches:
        path = os.path.join(target_dir, match.group("fname"))
        with open(path, "w") as file:
            file.write(match.group("code").strip())
        written_paths.append(path)
        if match.group("entry"):
            entry_path = path

    # Fall back to the last file if the model forgot to mark an entrypoint
    return written_paths, entry_path or written_paths[-1]

def execute_in_sandbox(target_filename: str, interactive: bool = False, cwd: str = None):
    """Runs the script inside a subprocess and returns execution data.

    Non-interactive (default): stdout/stderr are captured in memory so the
    harness can read them back and feed failures into the next retry.
    Interactive: the child inherits the real terminal's stdin/stdout/stderr
    directly, so input() prompts appear live and your keystrokes reach the
    script — but nothing is captured, so stderr/stdout come back empty and
    the auto-retry-on-crash feedback loop has nothing to work with.

    cwd lets multi-file attempts run with their sibling module(s) on the
    import path (Python auto-adds the executed script's own directory).
    """
    print(f"⚡ Testing code execution on {target_filename}...")
    try:
        if interactive:
            execution_result = subprocess.run(
                [sys.executable, target_filename],
                timeout=120,
                cwd=cwd
            )
            return execution_result.returncode, "", ""
        else:
            execution_result = subprocess.run(
                [sys.executable, target_filename],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd
            )
            return execution_result.returncode, execution_result.stderr, execution_result.stdout
    except subprocess.TimeoutExpired:
        return -1, "PROCESS_TIMEOUT: Script runtime exceeded maximum threshold.", ""

# =====================================================================
# PART 3: APPLICATION RUNTIME ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    user_task = input("Describe the code you want generated: ").strip()
    if not user_task:
        user_task = (
            "Write a Python script verifying the 'validate_email' logic. "
            "At the bottom, print a statement showing success if assert validate_email('user@domain.com') passes."
        )

    interactive_mode = input("Allow interactive input() in generated code? (y/N): ").strip().lower() == "y"

    print("====================================================")
    print(f"INITIALIZING HARNESS RUNTIME SYSTEM")
    print(f"Active Model Config: {LOCAL_MODEL}")
    print(f"Interactive Mode: {'ON' if interactive_mode else 'OFF (default)'}")
    print("====================================================")

    # Run the embedding retrieval once to fetch context for the prompt
    context = retrieve_relevant_context(user_task)
    
    runtime_traceback = ""
    max_attempts = 3
    success = False

    base_name, ext = os.path.splitext(SANDBOX_FILE)

    for iteration in range(max_attempts):
        print(f"\n🔄 --- CYCLE EXECUTION: {iteration + 1} of {max_attempts} ---")

        attempt_dir = f"{base_name}_attempt{iteration + 1}"

        raw_output = ask_local_model_for_code(
            user_task, reference_context=context, error_context=runtime_traceback, interactive=interactive_mode
        )
        written_files, entry_file = parse_and_write_files(raw_output, attempt_dir, default_filename=f"main{ext}")

        for path in written_files:
            with open(path) as f:
                marker = " (ENTRYPOINT)" if path == entry_file else ""
                print(f"\n📄 Generated file{marker} ({path}):\n{f.read()}")
        input("\nPress Enter to execute this code...")

        exit_code, stderr, stdout = execute_in_sandbox(
            os.path.basename(entry_file), interactive=interactive_mode, cwd=attempt_dir
        )

        if exit_code == 0:
            print(f"\n✅ SUCCESS: Validation complete under [{LOCAL_MODEL}] engine! (kept in {attempt_dir}/)")
            print(f"Output:\n{stdout.strip()}")
            success = True
            break
        else:
            print(f"\n❌ CRASH ENCOUNTERED on {entry_file}: Passing traceback logs back to model loop.")
            print(f"Traceback:\n{stderr.strip()}")
            runtime_traceback = stderr

    if not success:
        print(f"\n💥 LIMIT REACHED: Engine [{LOCAL_MODEL}] could not resolve syntax anomalies.")