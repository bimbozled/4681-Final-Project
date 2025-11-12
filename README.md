# 4681-Final-Project

## NL-SQL Assistant (Alpha)

Find better explaination [here](technical_report.md)

### Overview
This alpha prototype demonstrates a linear Natural Language to SQL flow using Snowflake Cortex Analyst. The goal is to keep the implementation simple while proving the end-to-end concept.

### Prerequisites
- Python 3.11 (tested)
- Access to a Snowflake account with Cortex Analyst enabled
- Semantic model deployed for Cortex Analyst

### Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```
   python -m pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your Snowflake credentials:
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_USER`
   - `SNOWFLAKE_PASSWORD`
   - `SNOWFLAKE_DATABASE`
   - `SNOWFLAKE_SCHEMA`
   - `SNOWFLAKE_WAREHOUSE`
4. Run the Streamlit app (use the same interpreter that installed dependencies):
   ```
   python -m streamlit run app.py
   ```

### Usage
1. Enter a natural language question in the text box.
2. Submit the query to trigger the enhancement and Cortex Analyst call.
3. Review:
   - The enhanced query text
   - The generated SQL statement
   - The result set returned from Snowflake
