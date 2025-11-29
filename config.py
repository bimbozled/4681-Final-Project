from __future__ import annotations

import os
from typing import Dict


def _is_snowflake_environment() -> bool:
    """
    Detect if running in Snowflake Native App or Streamlit in Snowsight environment.
    Checks for environment variables set by Snowflake.
    """
    # Native App environment variable
    if os.getenv("SNOWFLAKE_NATIVE_APP") == "true":
        return True
    # Native App name (set by Snowflake)
    if os.getenv("_SF_APP_NAME") is not None:
        return True
    # Streamlit in Snowsight - check for SNOWFLAKE_SESSION environment
    if os.getenv("SNOWFLAKE_SESSION") is not None:
        return True
    # Check if we're in Snowflake environment by checking sys.path
    # (Snowpark Session check removed to avoid connection errors)
    
    # Additional check: if we're in a path that looks like Snowflake
    import sys
    if any("snowflake" in str(path).lower() for path in sys.path):
        return True
    
    return False


class Settings:
    """
    Settings for Snowflake deployment.
    In Snowflake environment, uses current session (no credentials needed).
    """
    def __init__(self, is_snowflake_environment: bool = True) -> None:
        self.is_snowflake_environment = is_snowflake_environment

    def as_connection_kwargs(self) -> Dict[str, str]:
        """
        Return connection kwargs. In Snowflake environment, returns empty dict
        (connection uses current session automatically).
        """
        # In Snowflake, connection uses current session - no credentials needed
        return {}


def load_settings() -> Settings:
    """
    Load settings for Snowflake deployment.
    Uses session-based connection (no credentials needed).
    """
    is_snowflake = _is_snowflake_environment()
    
    if is_snowflake:
        # Snowflake environment: use session-based connection (no credentials needed)
        return Settings(is_snowflake_environment=True)
    
    # If not detected as Snowflake, assume it is anyway (for deployment)
    # This handles edge cases where detection might fail
    return Settings(is_snowflake_environment=True)

