"""
Step 4: feed prepared text (from either pdfplumber_method or
markdown_method -- this stage doesn't care which) to a local Ollama model
with a prompt asking for a fixed JSON schema, so the response is easy to
parse and to sanity-check. Model is a parameter, not a hardcoded global, so
different local models can be tried without editing this module.
"""

import json
import re

import ollama

from . import config


def extract_fields_with_llm(text: str, model: str = config.DEFAULT_MODEL) -> dict:
    prompt = (
        "Extract these financial fields from the annual report excerpt below. "
        "Return ONLY a JSON object with exactly these keys, no other text:\n"
        f"{json.dumps(config.FIELDS_SCHEMA, indent=2)}\n\n"
        "CRITICAL: only use a value if the exact figure is literally present "
        "in the excerpt text below. Do not use any outside knowledge you may "
        "have about this company's real-world financial results -- if a "
        "field's figure does not literally appear in the excerpt, you MUST "
        "return null for it, even if you believe you know the real number. "
        "A null is the correct, expected answer when the excerpt simply "
        "doesn't contain that figure; a null is preferred to a "
        "remembered/guessed number.\n\n"
        "If a field isn't present in the excerpt, use null. Use the most "
        "recent year's figures if multiple years are shown. Some figures "
        "appear in both INR and USD (e.g. for ADR holders) -- always report "
        "the INR (Rs./₹) value, never the USD equivalent. 'Earnings per "
        "equity share' is usually reported as two separate figures, Basic "
        "and Diluted -- put them in eps_basic and eps_diluted respectively, "
        "don't merge them into one value.\n\n"
        "A page may start with a '[UNIT NOTE: ...]' line -- this means every "
        "bare figure on that page (no currency symbol or unit of its own) is "
        "stated in that unit. When you use such a bare figure for a "
        "currency field (share_capital, sales, revenue, gross_profit, "
        "net_profit, dividend), append that unit to the value you return, "
        "e.g. a bare '928,093' on a page noted '[UNIT NOTE: ... ₹ million "
        "...]' should be returned as '₹928,093 million'.\n\n"
        "--- EXCERPT ---\n"
        f"{text[:12000]}"  # keep the request bounded even if page selection over-collects
    )
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    content = response["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(match.group(0)) if match else {"error": "unparseable response", "raw": content}
