from dotenv import load_dotenv
load_dotenv()
from langchain_ollama import OllamaLLM
from prompts import SYSTEM_PROMPT, DEBUG_PROMPT
from python_executor import run_code

MAX_RETRIES = 5

llm = OllamaLLM(model="deepseek-coder:6.7b")

user_task = """
Create a Python script that:
1. Reads the CSV file "employees.csv" (columns: name, salary)
2. Calculates the average salary
3. Displays the result
"""


def strip_code_fence(text: str) -> str:
    """Remove a leading/trailing ```python fenced block, if the model added one."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# generate code, run it, check for errors, fix them, and try again.
def generate_code(prompt):
    return strip_code_fence(llm.invoke(prompt))

code_prompt = f"""
{SYSTEM_PROMPT}

TASK:
{user_task}
"""

generated_code = generate_code(code_prompt)

for attempt in range(MAX_RETRIES):
    #   - previousl generated_code.py is overwritten each attempt and left after the run
    with open("generated_code.py", "w") as f:
        f.write(generated_code)

    result = run_code("generated_code.py")

    if result["success"]:
        print("\nFINAL WORKING CODE:\n")
        print(generated_code)

        print("\nOUTPUT:\n")
        print(result["output"])

        break

    print(f"\nAttempt {attempt + 1} failed...")
    print(result["error"])

    debug_prompt = DEBUG_PROMPT.format(
        code=generated_code,
        error=result["error"]
    )

    generated_code = generate_code(debug_prompt)

else:
    print("Agent failed after maximum retries.")



""" Create a Python script that:
1. Reads a CSV file
2. Calculates average salary
3. Displays the result """
