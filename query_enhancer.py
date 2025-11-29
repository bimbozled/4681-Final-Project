from __future__ import annotations

from datetime import date
from typing import Dict


ABBREVIATIONS: Dict[str, str] = {
    "rev": "revenue",
    "qty": "quantity",
    "avg": "average",
}


def enhance_query(query: str, today: date | None = None) -> str:
    """
    Apply lightweight, deterministic enhancements to the user's question.
    - Normalize whitespace
    - Lowercase the text
    - Expand a small set of abbreviations
    - Add the current date for context
    """
    normalized = query.strip()
    today = today or date.today()

    lowered = normalized.lower()
    tokens = lowered.split()
    expanded_tokens = [ABBREVIATIONS.get(token, token) for token in tokens]
    expanded = " ".join(expanded_tokens)

    if expanded:
        contextualized = f"{expanded}. Assume current date is {today.isoformat()}."
    else:
        contextualized = f"Assume current date is {today.isoformat()}."

    return contextualized

