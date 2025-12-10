from __future__ import annotations

import collections
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    trace_id: str
    timestamp: str
    user_query: str
    enhanced_query: str
    generated_sql: str
    status: str
    error_message: Optional[str]
    total_latency_ms: int
    row_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MetricsCollector:
    """In-memory metrics collector."""
    
    def __init__(self) -> None:
        self._queries: List[QueryMetrics] = []
        self._max_queries = 100
        self._counts: collections.defaultdict[str, int] = collections.defaultdict(int)
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """Record query metrics."""
        self._queries.append(metrics)
        self._counts[metrics.status] += 1
        
        if len(self._queries) > self._max_queries:
            removed = self._queries.pop(0)
            self._counts[removed.status] -= 1
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent queries as list of dictionaries."""
        recent = self._queries[-limit:]
        return [q.to_dict() for q in reversed(recent)]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total = len(self._queries)
        success = self._counts.get("success", 0)
        error = self._counts.get("error", 0)
        
        success_rate = (success / total * 100) if total > 0 else 0.0
        
        total_latency = sum(q.total_latency_ms for q in self._queries)
        avg_latency_ms = int(total_latency / total) if total > 0 else 0
        
        return {
            "total": total,
            "success": success,
            "error": error,
            "success_rate": round(success_rate, 1),
            "avg_latency_ms": avg_latency_ms
        }
    
    def get_query_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get query metrics by trace ID."""
        for query in self._queries:
            if query.trace_id == trace_id:
                return query.to_dict()
        return None
    
    def get_all_trace_ids(self) -> List[str]:
        """Get all stored trace IDs."""
        return [q.trace_id for q in self._queries]


_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Get the global metrics collector singleton."""
    return _collector

