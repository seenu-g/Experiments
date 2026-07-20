import pandas as pd
import requests
import json

# The schema our downstream database strictly requires
EXPECTED_SCHEMA = ["transaction_id", "customer_email", "purchase_amount", "purchase_date"]

# The messy data we actually received today
incoming_data = pd.DataFrame({
    "txn_id": ["A1", "A2"],
    "email_address": ["alice@test.com", "bob@test.com"],
    "total_cost": [150.00, 89.50],
    "date": ["2026-05-26", "2026-05-26"]
})

ADAPT_RECOVER_PROMPT = """
    You are a data engineer system. Your job is to map actual data columns to the expected schema.

    Expected columns: {expected_cols}
    Actual columns: {actual_cols}

    Match the actual columns to the expected columns based on semantic meaning.
    Return ONLY a valid JSON object where the keys are the actual columns and the values are the expected columns.
    Do not include any markdown, explanations, or text outside the JSON.
    """

def detect_mismatch(df, expected_schema):
    """Return True if df's columns don't exactly match the expected schema."""
    return set(df.columns) != set(expected_schema)


def get_healing_model() -> str:
    """Return the local Ollama model used for schema healing."""
    return "phi3"


def heal_schema(expected_cols, actual_cols):
    """
    Asks a local LLM to map unknown columns to the expected schema.
    """
    prompt = ADAPT_RECOVER_PROMPT.format(expected_cols=expected_cols, actual_cols=actual_cols)

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": get_healing_model(),
        "prompt": prompt,
        "stream": False,
        "format": "json" # This forces Ollama to output valid JSON
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        # Extract the JSON string from the response
        result_text = response.json().get("response", "{}")
        mapping = json.loads(result_text)
        return mapping
        
    except Exception as e:
        print(f"CRITICAL: LLM healing failed. Error: {e}")
        return None

def fix_mismatch(df, expected_schema):
    """Ask the LLM to map df's columns onto expected_schema and apply the mapping.

    Raises RuntimeError if the LLM fails to return a mapping, or KeyError if the
    mapping maps two different actual columns to the same expected name.
    """
    actual_cols = list(df.columns)
    mapping = heal_schema(expected_schema, actual_cols)

    if not mapping:
        raise RuntimeError("Self-healing failed to return a valid mapping.")

    print(f"Healing successful. Applying mapping: {mapping}")

    # Verify the LLM didn't map two different actual columns to the same
    # expected name, which would silently rename() into duplicate columns.
    target_cols = list(mapping.values())
    if len(target_cols) != len(set(target_cols)):
        duplicates = {col for col in target_cols if target_cols.count(col) > 1}
        print(f"ERROR: Healing produced duplicate target columns: {duplicates}")
        raise KeyError("Unrecoverable schema drift.")

    df = df.rename(columns=mapping)

    # Drop any columns the LLM didn't map to the expected schema (e.g. extra
    # source fields with no semantic match) so unexpected data doesn't
    # silently ride along downstream.
    extra_cols = [col for col in df.columns if col not in expected_schema]
    if extra_cols:
        print(f"WARNING: Dropping unmapped extra columns: {extra_cols}")
        df = df.drop(columns=extra_cols)

    return df


def confirm_healing(df, expected_schema):
    """Return True if df now contains every expected column, False otherwise."""
    missing_cols = [col for col in expected_schema if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Healing incomplete. Still missing: {missing_cols}")
        return False
    return True


def process_data(df, expected_schema):
    if not detect_mismatch(df, expected_schema):
        print("Schema validation passed. Proceeding with pipeline...")
        return df[expected_schema]

    print("WARNING: Schema mismatch detected. Initiating self-healing...")
    healed_df = fix_mismatch(df, expected_schema)

    if not confirm_healing(healed_df, expected_schema):
        # Trigger PagerDuty/Email alert here
        raise KeyError("Unrecoverable schema drift.")

    print("Pipeline successfully healed. Continuing data transformations...")
    return healed_df[expected_schema]

# Run the pipeline
healed_df = process_data(incoming_data, EXPECTED_SCHEMA)
print("\nFinal DataFrame:")
print(healed_df.head())