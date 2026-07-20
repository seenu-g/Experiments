from pathlib import Path

import requests

from sqlite3_helper import (
    model,
    sql_db_list_tables,
    sql_db_query,
    sql_db_query_checker,
    sql_db_schema,
)

CHINOOK_URL = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
CHINOOK_PATH = Path("Chinook.db")


def ensure_chinook_db(path: Path = CHINOOK_PATH, url: str = CHINOOK_URL) -> Path:
    """Download Chinook.db if it isn't already present."""
    if path.exists():
        print(f"{path} already exists, skipping download.")
        return path
    response = requests.get(url, timeout=60)
    if response.status_code == 200:
        path.write_bytes(response.content)
        print(f"File downloaded and saved as {path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
    return path


def strip_code_fence(text: str) -> str:
    """Remove a leading/trailing ```sql fenced block, if the model added one."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def list_tables_step() -> str:
    """Step 1: list all tables in the database."""
    return sql_db_list_tables.invoke("")


def schema_step(tables: str, question: str) -> tuple[str, str]:
    """Step 2: ask the model which tables are relevant, then fetch their schema."""
    relevant_tables = model.invoke(
        f"Available tables: {tables}\n"
        f"Question: {question}\n"
        "List only the table names (comma-separated) needed to answer this question. "
        "Output only the table names, nothing else."
    ).text.strip()
    schema = sql_db_schema.invoke(relevant_tables)
    return relevant_tables, schema


def draft_query_step(schema: str, question: str) -> str:
    """Step 3: ask the model to draft a SQL query from the schema and question."""
    return strip_code_fence(
        model.invoke(
            f"Schema:\n{schema}\n\n"
            f"Question: {question}\n"
            "Write a single syntactically correct sqlite SELECT query (limit to at most "
            "5 results unless the question asks for a specific number) to answer the "
            "question. Output only the SQL query, nothing else."
        ).text
    )


def checker_step(draft_query: str) -> str:
    """Step 4: validate/fix the draft query."""
    return strip_code_fence(sql_db_query_checker.invoke(draft_query))


def run_query_step(checked_query: str) -> str:
    """Step 5: execute the checked query against the database."""
    return sql_db_query.invoke(checked_query)


def answer_step(question: str, result: str) -> str:
    """Step 6: turn the raw query result into a natural-language answer."""
    return model.invoke(
        f"Question: {question}\n"
        f"Query result: {result}\n"
        "Give a concise natural-language answer using only this result."
    ).text.strip()


def run_pipeline(question: str) -> str:
    """Run all six steps in sequence, printing progress, and return the final answer."""
    print(f"Question: {question}\n")

    print("Step 1: sql_db_list_tables")
    tables = list_tables_step()
    print(tables, "\n", flush=True)

    print("Step 2: pick relevant tables + sql_db_schema")
    relevant_tables, schema = schema_step(tables, question)
    print("Relevant tables:", relevant_tables)
    print(schema, "\n", flush=True)

    print("Step 3: draft SQL query")
    draft_query = draft_query_step(schema, question)
    print(draft_query, "\n", flush=True)

    print("Step 4: sql_db_query_checker")
    checked_query = checker_step(draft_query)
    print(checked_query, "\n", flush=True)

    print("Step 5: sql_db_query")
    result = run_query_step(checked_query)
    print(result, "\n", flush=True)

    print("Step 6: final answer")
    answer = answer_step(question, result)
    print(answer, flush=True)
    return answer


if __name__ == "__main__":
    ensure_chinook_db()
    run_pipeline("Which genre on average has the longest tracks?")
