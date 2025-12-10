from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from tracer import get_trace_id


_logger = logging.getLogger("edw_assistant")
_logger.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_handler.setLevel(logging.INFO)

_formatter = logging.Formatter("%(message)s")
_handler.setFormatter(_formatter)

_logger.addHandler(_handler)
_logger.propagate = False


def log_event(step: str, level: str = "INFO", **kwargs: Any) -> None:
    """Log structured JSON event with trace_id."""
    trace_id = get_trace_id()
    
    log_data: Dict[str, Any] = {
        "timestamp": time.time(),
        "trace_id": trace_id,
        "step": step,
        **kwargs
    }
    
    log_json = json.dumps(log_data)
    
    if level == "ERROR":
        _logger.error(log_json)
    elif level == "WARNING":
        _logger.warning(log_json)
    else:
        _logger.info(log_json)


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, step: str) -> None:
        self.step = step
        self.start_time: float | None = None
    
    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is not None:
            latency_ms = int((time.time() - self.start_time) * 1000)
            log_event(f"{self.step}_completed", latency_ms=latency_ms)

