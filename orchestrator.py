from __future__ import annotations

from typing import Any, Dict

from snowflake.snowpark import Session

from config import load_settings
from cortex_client import CortexClient, CortexClientError
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

    def run(self, user_query: str) -> Dict[str, Any]:
        if not user_query.strip():
            raise ValueError("Query cannot be empty.")

        enhanced = enhance_query(user_query)

        try:
            cortex_result = self._client.generate_sql_and_results(enhanced)
        except CortexClientError:
            raise

        return {
            "enhanced_query": enhanced,
            "generated_sql": cortex_result.get("generated_sql", ""),
            "rows": cortex_result.get("rows", []),
            "table_schema": cortex_result.get("table_schema", ""),  # Pass through schema
        }