"""Small response-cleaning helpers shared by all LLM providers."""

from __future__ import annotations

import re


def extract_sql(text: str) -> str:
    """Remove common model wrappers while preserving one SQL statement.

    The SQL validator remains the security boundary. This helper only cleans
    presentation noise such as markdown fences and introductory prose.
    """
    value = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", value, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        value = fenced.group(1).strip()

    select_index = value.lower().find("select")
    with_index = value.lower().find("with")
    candidates = [index for index in (select_index, with_index) if index >= 0]
    if candidates:
        value = value[min(candidates) :]

    return value.strip().rstrip(";")
