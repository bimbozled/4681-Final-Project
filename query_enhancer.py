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
    - Only add date context if query mentions date/time-related terms
    """
    normalized = query.strip()
    today = today or date.today()

    lowered = normalized.lower()
    tokens = lowered.split()
    expanded_tokens = [ABBREVIATIONS.get(token, token) for token in tokens]
    expanded = " ".join(expanded_tokens)

    date_keywords = ["date", "time", "today", "yesterday", "week", "month", "year", "ago", "recent", "latest", "last"]
    needs_date_context = any(keyword in expanded for keyword in date_keywords)

    if needs_date_context:
        contextualized = f"{expanded}. (Current date is {today.isoformat()})"
    else:
        contextualized = expanded

    return contextualized

