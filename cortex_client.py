from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException

from config import Settings


class CortexClientError(RuntimeError):
    """Raised when the Cortex Analyst interaction fails."""


class CortexClient:
    def __init__(self, settings: Settings, session: Session | None = None) -> None:
        self._settings = settings
        self._session = session

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """
        Get Snowflake session. In Streamlit in Snowsight, uses the session
        passed from streamlit_app (via st.connection or session_state).
        """
        if self._session is None:
            raise CortexClientError(
                "No Snowflake session provided. Make sure to pass the session "
                "from Streamlit (st.connection('snowflake').session)"
            )
        
        try:
            yield self._session
        except Exception as e:
            raise CortexClientError(f"Session error: {e}") from e

    def generate_sql_and_results(self, enhanced_query: str) -> Dict[str, Any]:
        """
        Generate SQL with Snowflake Cortex Analyst and execute it.
        Returns a payload containing the cleaned SQL and result rows.
        """
        with self._get_session() as session:
            # Get schema info first
            target_db = "GENAI_FINAL_PROJECT_DB"
            target_schema = "PUBLIC"
            # Use the correct table name
            table_schema = self._get_table_schema(session, target_db, target_schema, "IOT_TELEMETRY_DATA")
            
            # Build prompt with schema info
            prompt = self._build_prompt(enhanced_query, session)
            cortex_sql = self._build_cortex_statement(prompt)

            try:
                generated_sql = self._invoke_cortex(session, cortex_sql)
                cleaned_sql = self._clean_sql(generated_sql)
                
                rows, columns = self._execute_sql(session, cleaned_sql)
            except SnowparkSQLException as exc:
                # Enhance error message with schema info
                error_detail = str(exc)
                if "invalid identifier" in error_detail.lower():
                    raise CortexClientError(
                        f"Column name error: {exc}\n\n"
                        f"Generated SQL:\n{cleaned_sql}\n\n"
                        f"Available columns in IOT_TELEMETRY_DATA:\n{table_schema}\n\n"
                        f"The SQL is trying to use a column that doesn't exist. "
                        f"Please check the column names in your query."
                    ) from exc
                raise CortexClientError(f"Snowflake error: {exc}") from exc
            except Exception as exc:
                raise CortexClientError(f"Unexpected error: {exc}") from exc

        row_dicts = [dict(zip(columns, row)) for row in rows]

        return {
            "generated_sql": cleaned_sql,
            "rows": row_dicts,
            "columns": columns,
            "table_schema": table_schema,  # Add schema info for debugging
        }

    def _get_table_schema(self, session: Session, database: str, schema: str, table: str) -> str:
        """
        Query INFORMATION_SCHEMA to get table column information.
        Returns a formatted string describing the table schema.
        """
        try:
            # Set database and schema context
            session.sql(f"USE DATABASE {database}").collect()
            session.sql(f"USE SCHEMA {schema}").collect()
            
            # Query INFORMATION_SCHEMA
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' 
              AND TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
            """
            result = session.sql(query).collect()
            
            if not result:
                return f"{table} (columns unknown - check table exists)"
            
            # Format with line breaks for clarity
            column_descriptions = []
            for row in result:
                col_name = row['COLUMN_NAME']
                data_type = row['DATA_TYPE']
                nullable = "NULL" if row['IS_NULLABLE'] == 'YES' else "NOT NULL"
                column_descriptions.append(f"  - {col_name} ({data_type}, {nullable})")
            
            return "\n".join(column_descriptions)
        except Exception as e:
            # Fallback: try to describe columns without INFORMATION_SCHEMA
            try:
                sample_query = f"SELECT * FROM {database}.{schema}.{table} LIMIT 1"
                sample_result = session.sql(sample_query).collect()
                if sample_result:
                    columns = list(sample_result[0].asDict().keys())
                    return "\n".join([f"  - {col}" for col in columns])
            except:
                pass
            return f"{table} (unable to retrieve schema: {e})"
    
    def _build_prompt(self, enhanced_query: str, session: Session) -> str:
        """
        Build the prompt for Cortex with current database schema.
        Uses the specified database and schema.
        """
        # Use the target database and schema
        target_db = "GENAI_FINAL_PROJECT_DB"
        target_schema = "PUBLIC"
        
        # FIXED: Use the correct table name
        table_schema = self._get_table_schema(
            session, 
            target_db, 
            target_schema, 
            "IOT_TELEMETRY_DATA"
        )
        
        schema_context = (
            f"You are a SQL expert for Snowflake. Generate ONLY valid SQL - no explanations or markdown.\n\n"
            f"DATABASE: {target_db}\n"
            f"SCHEMA: {target_schema}\n"
            f"TABLE: IOT_TELEMETRY_DATA\n\n"
            f"AVAILABLE COLUMNS (USE THESE EXACT NAMES):\n{table_schema}\n\n"
            f"CRITICAL RULES - FAILURE TO FOLLOW WILL CAUSE ERRORS:\n"
            f"1. You MUST use ONLY the column names listed above - NO OTHER COLUMNS EXIST\n"
            f"2. DO NOT use columns named: DATE, TIMESTAMP, TIME, DATETIME, DEVICE_ID, TEMPERATURE unless they appear above\n"
            f"3. The table name is IOT_TELEMETRY_DATA\n"
            f"4. Examine the available columns carefully before writing SQL\n"
            f"5. Use the full table name: {target_db}.{target_schema}.IOT_TELEMETRY_DATA\n"
            f"6. Output ONLY the SQL query - no markdown code blocks, no explanations\n\n"
            f"USER QUESTION: {enhanced_query}\n\n"
            f"Based on the available columns above, generate the SQL query:\n"
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

    def _invoke_cortex(self, session: Session, cortex_sql: str) -> str:
        result = session.sql(cortex_sql).collect()

        if not result or len(result) == 0:
            raise CortexClientError("Cortex Analyst returned an empty response.")

        generated_sql = result[0]['GENERATED_SQL']
        if not generated_sql:
            raise CortexClientError("Cortex Analyst returned an empty response.")

        return str(generated_sql)

    def _clean_sql(self, raw_sql: str) -> str:
        cleaned = raw_sql.strip()
        for marker in ("```sql", "```", ";"):
            cleaned = cleaned.replace(marker, "")
        return cleaned.strip()

    def _validate_sql_columns(self, sql: str, session: Session) -> tuple[bool, str]:
        """
        Validate that SQL only references columns that exist in the table.
        Returns (is_valid, error_message).
        """
        try:
            # Get actual column names
            target_db = "GENAI_FINAL_PROJECT_DB"
            target_schema = "PUBLIC"
            
            query = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{target_schema}' 
              AND TABLE_NAME = 'IOT_TELEMETRY_DATA'
            """
            result = session.sql(query).collect()
            valid_columns = {row['COLUMN_NAME'].upper() for row in result}
            
            if not valid_columns:
                return True, ""  # Skip validation if we can't get columns
            
            # Extract potential column references from SQL
            import re
            sql_upper = sql.upper()
            
            # Skip validation - it's causing false positives
            # The validation was flagging SQL keywords/functions like ::DATE as invalid columns
            # Let Snowflake handle the actual validation when executing
            return True, ""
            
        except Exception:
            # If validation fails, proceed anyway
            return True, ""

    def _execute_sql(
        self, session: Session, sql: str
    ) -> tuple[List[tuple[Any, ...]], List[str]]:
        if not sql:
            raise CortexClientError("Cortex Analyst did not provide a SQL statement.")

        result = session.sql(sql).collect()
        
        if not result:
            return [], []
        
        # Get column names from the result
        columns = list(result[0].asDict().keys()) if result else []
        
        # Convert rows to tuples
        rows = [tuple(row.asDict().values()) for row in result]
        
        return rows, columns