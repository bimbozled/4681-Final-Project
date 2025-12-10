from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from snowflake.snowpark import Session

from config import load_settings
from cortex_client import CortexClient, CortexClientError
from logger import Timer, log_event
from metrics import QueryMetrics, get_collector
from query_enhancer import enhance_query


class Orchestrator:
    def __init__(self, cortex_client: CortexClient) -> None:
        self._client = cortex_client

    @classmethod
    def from_session(cls, session: Session) -> "Orchestrator":
        """
        Create orchestrator from a Snowflake session (for Streamlit in Snowsight).
        """
        settings = load_settings()
        client = CortexClient(settings, session=session)
        return cls(client)

    def run(self, user_query: str, trace_id: str) -> Dict[str, Any]:
        if not user_query.strip():
            raise ValueError("Query cannot be empty.")

        start_time = time.time()
        status = "error"
        error_message: str | None = None
        generated_sql = ""
        row_count = 0
        enhanced = ""
        rows: list[Any] = []
        table_schema = ""

        try:
            log_event("query_start", user_query=user_query)
            
            with Timer("enhance"):
                enhanced = enhance_query(user_query)
            
            log_event("enhanced", enhanced_query=enhanced)
            
            with Timer("cortex_total"):
                cortex_result = self._client.generate_sql_and_results(enhanced)
            
            generated_sql = cortex_result.get("generated_sql", "")
            rows = cortex_result.get("rows", [])
            row_count = len(rows)
            table_schema = cortex_result.get("table_schema", "")
            
            status = "success"
            log_event("query_success", row_count=row_count)
            
        except CortexClientError as exc:
            error_message = str(exc)
            error_type = type(exc).__name__
            log_event("query_error", level="ERROR", error=error_message, error_type=error_type)
            raise
        except Exception as exc:
            error_message = str(exc)
            error_type = type(exc).__name__
            log_event("query_error", level="ERROR", error=error_message, error_type=error_type)
            raise
        finally:
            total_latency_ms = int((time.time() - start_time) * 1000)
            metrics = QueryMetrics(
                trace_id=trace_id,
                timestamp=datetime.now().isoformat(),
                user_query=user_query,
                enhanced_query=enhanced,
                generated_sql=generated_sql,
                status=status,
                error_message=error_message,
                total_latency_ms=total_latency_ms,
                row_count=row_count
            )
            get_collector().record_query(metrics)

        return {
            "enhanced_query": enhanced,
            "generated_sql": generated_sql,
            "rows": rows,
            "table_schema": table_schema,
            "trace_id": trace_id,
        }