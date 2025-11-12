from __future__ import annotations

import streamlit as st

from cortex_client import CortexClientError
from orchestrator import Orchestrator


def main() -> None:
    st.set_page_config(page_title="NL-SQL Assistant (Alpha)", layout="wide")
    st.title("NL-SQL Assistant (Alpha)")
    st.caption("Natural language to Snowflake SQL using Cortex Analyst.")

    query_input = st.text_area("Ask a question about your data", height=150)

    if st.button("Run Query", type="primary"):
        if not query_input.strip():
            st.error("Please enter a question before running the assistant.")
            return

        try:
            orchestrator = Orchestrator.from_env()
        except RuntimeError as exc:
            st.error(f"Configuration error: {exc}")
            return

        try:
            result = orchestrator.run(query_input)
        except CortexClientError as exc:
            st.error(f"Cortex error: {exc}")
            return
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            return

        st.subheader("Enhanced Query")
        st.code(result["enhanced_query"])

        st.subheader("Generated SQL")
        generated_sql = result["generated_sql"]
        if generated_sql:
            st.code(generated_sql, language="sql")
        else:
            st.write("No SQL generated. Check Cortex Analyst configuration.")

        st.subheader("Results")
        rows = result["rows"]
        if rows:
            st.dataframe(rows)
        else:
            st.write("No rows returned.")


if __name__ == "__main__":
    main()

