from __future__ import annotations

from contextvars import ContextVar
from typing import Optional
from uuid import uuid4

_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def generate_trace_id() -> str:
    """Generate a new trace ID (8 characters from UUID)."""
    full_uuid = str(uuid4())
    return full_uuid[:8]


def set_trace_id(trace_id: str) -> None:
    """Store trace ID in context."""
    _trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Retrieve trace ID from context."""
    return _trace_id_var.get()

