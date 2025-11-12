from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

import snowflake.connector
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import ProgrammingError

from config import Settings


class CortexClientError(RuntimeError):
    """Raised when the Cortex Analyst interaction fails."""


class CortexClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @contextmanager
    def _connection(self) -> Iterator[SnowflakeConnection]:
        connection = snowflake.connector.connect(
            **self._settings.as_connection_kwargs()
        )
        try:
            yield connection
        finally:
            connection.close()

    def generate_sql_and_results(self, enhanced_query: str) -> Dict[str, Any]:
        """
        Generate SQL with Snowflake Cortex Analyst and execute it.
        Returns a payload containing the cleaned SQL and result rows.
        """
        prompt = self._build_prompt(enhanced_query)
        cortex_sql = self._build_cortex_statement(prompt)

        with self._connection() as connection:
            try:
                generated_sql = self._invoke_cortex(connection, cortex_sql)
                cleaned_sql = self._clean_sql(generated_sql)
                rows, columns = self._execute_sql(connection, cleaned_sql)
            except ProgrammingError as exc:
                raise CortexClientError(f"Snowflake error: {exc}") from exc

        row_dicts = [dict(zip(columns, row)) for row in rows]

        return {
            "generated_sql": cleaned_sql,
            "rows": row_dicts,
            "columns": columns,
        }

    def _build_prompt(self, enhanced_query: str) -> str:
        schema_context = (
            "You are a SQL expert for Snowflake. Given this database schema:\n\n"
            "TABLES:\n"
            "- ORDERS: O_ORDERKEY (int), O_CUSTKEY (int), O_ORDERSTATUS (varchar), "
            "O_TOTALPRICE (decimal), O_ORDERDATE (date)\n"
            "- CUSTOMER: C_CUSTKEY (int), C_NAME (varchar), C_ADDRESS (varchar), "
            "C_PHONE (varchar)\n"
            "- LINEITEM: L_ORDERKEY (int), L_PARTKEY (int), L_QUANTITY (int), "
            "L_EXTENDEDPRICE (decimal)\n\n"
            f"User question: {enhanced_query}\n\n"
            "Generate ONLY the SQL query to answer this question. "
            "No explanation, no markdown, just the SQL statement."
        )
        return schema_context

    def _build_cortex_statement(self, prompt: str) -> str:
        escaped_prompt = prompt.replace("'", "''")
        return (
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(\n"
            "    'mistral-large',\n"
            f"    '{escaped_prompt}'\n"
            ") AS generated_sql"
        )

    def _invoke_cortex(self, connection: SnowflakeConnection, cortex_sql: str) -> str:
        with connection.cursor() as cursor:
            cursor.execute(cortex_sql)
            result = cursor.fetchone()

        if not result or not result[0]:
            raise CortexClientError("Cortex Analyst returned an empty response.")

        return str(result[0])

    def _clean_sql(self, raw_sql: str) -> str:
        cleaned = raw_sql.strip()
        for marker in ("```sql", "```", ";"):
            cleaned = cleaned.replace(marker, "")
        return cleaned.strip()

    def _execute_sql(
        self, connection: SnowflakeConnection, sql: str
    ) -> tuple[List[tuple[Any, ...]], List[str]]:
        if not sql:
            raise CortexClientError("Cortex Analyst did not provide a SQL statement.")

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            description = cursor.description or []

        columns = [column[0] for column in description]
        return rows, columns
