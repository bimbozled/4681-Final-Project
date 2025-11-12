from __future__ import annotations

import os
from typing import Dict

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError


class Settings(BaseModel):
    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_warehouse: str

    def as_connection_kwargs(self) -> Dict[str, str]:
        return {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "password": self.snowflake_password,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            "warehouse": self.snowflake_warehouse,
        }


def load_settings() -> Settings:
    """
    Load environment variables, validate them, and return Settings.
    Fail fast with a clear message if any required variable is missing.
    """
    load_dotenv()

    raw_values: Dict[str, str | None] = {
        "snowflake_account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "snowflake_user": os.getenv("SNOWFLAKE_USER"),
        "snowflake_password": os.getenv("SNOWFLAKE_PASSWORD"),
        "snowflake_database": os.getenv("SNOWFLAKE_DATABASE"),
        "snowflake_schema": os.getenv("SNOWFLAKE_SCHEMA"),
        "snowflake_warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    }

    missing = [key for key, value in raw_values.items() if not value]
    if missing:
        readable = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {readable}. "
            "Populate .env using .env.example."
        )

    try:
        return Settings(**raw_values)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise RuntimeError(f"Invalid configuration: {exc}") from exc

