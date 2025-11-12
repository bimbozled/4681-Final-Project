# Snowflake Cortex Configuration - PRODUCTION MODE

## ✅ Cortex AI is ENABLED and WORKING

## Connection Details
- Account: yqc42692.us-east-1
- Database: SNOWFLAKE_SAMPLE_DATA
- Schema: TPCH_SF1
- Warehouse: COMPUTE_WH
- User: ACCOUNTADMIN

## Cortex Complete Function

### Working Syntax
```python
sql = f"""
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    'You are a SQL expert for Snowflake. Given this database schema:

TABLES:
- ORDERS: O_ORDERKEY (int), O_CUSTKEY (int), O_ORDERSTATUS (varchar), O_TOTALPRICE (decimal), O_ORDERDATE (date)
- CUSTOMER: C_CUSTKEY (int), C_NAME (varchar), C_ADDRESS (varchar), C_PHONE (varchar)
- LINEITEM: L_ORDERKEY (int), L_PARTKEY (int), L_QUANTITY (int), L_EXTENDEDPRICE (decimal)

User question: {enhanced_query}

Generate ONLY the SQL query to answer this question. No explanation, no markdown, just the SQL statement.'
) AS generated_sql
"""
```

### Response Format
- Returns a string containing the SQL query
- Need to parse/clean it (remove any extra text if present)
- Execute the extracted SQL on SNOWFLAKE_SAMPLE_DATA.TPCH_SF1

## Implementation Steps

### 1. Query Enhancement (query_enhancer.py)
```python
def enhance_query(user_query: str) -> str:
    """
    Add context and clarify query.
    """
    enhanced = user_query.strip()
    
    # Add table context if not specified
    if 'order' in enhanced.lower() and 'table' not in enhanced.lower():
        enhanced += " (use ORDERS table)"
    
    if 'customer' in enhanced.lower() and 'table' not in enhanced.lower():
        enhanced += " (use CUSTOMER table)"
    
    # Add current date context if relevant
    if 'recent' in enhanced.lower() or 'latest' in enhanced.lower():
        from datetime import datetime
        enhanced += f" (current date: {datetime.now().strftime('%Y-%m-%d')})"
    
    return enhanced
```

### 2. Cortex Client (cortex_client.py)
```python
import snowflake.connector
from typing import Dict, Any

def generate_sql_with_cortex(connection, enhanced_query: str) -> str:
    """
    Use Cortex to generate SQL from natural language.
    """
    cursor = connection.cursor()
    
    prompt = f"""You are a SQL expert for Snowflake. Given this database schema:

TABLES:
- ORDERS: O_ORDERKEY (int), O_CUSTKEY (int), O_ORDERSTATUS (varchar), O_TOTALPRICE (decimal), O_ORDERDATE (date)
- CUSTOMER: C_CUSTKEY (int), C_NAME (varchar), C_ADDRESS (varchar), C_PHONE (varchar)  
- LINEITEM: L_ORDERKEY (int), L_PARTKEY (int), L_QUANTITY (int), L_EXTENDEDPRICE (decimal)

User question: {enhanced_query}

Generate ONLY the SQL query to answer this question. No explanation, no markdown, just the SQL statement."""

    cortex_query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large',
        '{prompt.replace("'", "''")}'
    ) AS generated_sql
    """
    
    cursor.execute(cortex_query)
    result = cursor.fetchone()
    
    # Clean the SQL (remove markdown, extra text)
    sql = result[0].strip()
    sql = sql.replace('```sql', '').replace('```', '').strip()
    
    return sql

def execute_sql(connection, sql: str) -> Dict[str, Any]:
    """
    Execute the generated SQL and return results.
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Get results
    rows = cursor.fetchall()
    
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows)
    }
```

### 3. Full Workflow (orchestrator.py)
```python
from query_enhancer import enhance_query
from cortex_client import get_snowflake_connection, generate_sql_with_cortex, execute_sql

def process_user_query(user_query: str) -> Dict[str, Any]:
    """
    Main orchestrator: enhance → generate SQL → execute → return results
    """
    # Step 1: Enhance query
    enhanced_query = enhance_query(user_query)
    
    # Step 2: Connect to Snowflake
    connection = get_snowflake_connection()
    
    try:
        # Step 3: Generate SQL using Cortex
        generated_sql = generate_sql_with_cortex(connection, enhanced_query)
        
        # Step 4: Execute SQL
        results = execute_sql(connection, generated_sql)
        
        return {
            "original_query": user_query,
            "enhanced_query": enhanced_query,
            "generated_sql": generated_sql,
            "results": results,
            "error": None
        }
    
    except Exception as e:
        return {
            "original_query": user_query,
            "enhanced_query": enhanced_query,
            "generated_sql": None,
            "results": None,
            "error": str(e)
        }
    
    finally:
        connection.close()
```

## Sample Queries for Testing

1. "How many orders are there?"
   - Expected SQL: `SELECT COUNT(*) FROM ORDERS`

2. "What is the total revenue?"
   - Expected SQL: `SELECT SUM(O_TOTALPRICE) FROM ORDERS`

3. "How many customers do we have?"
   - Expected SQL: `SELECT COUNT(DISTINCT C_CUSTKEY) FROM CUSTOMER`

4. "Show me orders from 1995"
   - Expected SQL: `SELECT * FROM ORDERS WHERE YEAR(O_ORDERDATE) = 1995 LIMIT 10`

## Environment Variables (.env)
```
SNOWFLAKE_ACCOUNT=yqc42692.us-east-1
SNOWFLAKE_USER=ACCOUNTADMIN
SNOWFLAKE_PASSWORD=your_password_here
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

## Notes
- Use mistral-large model (proven to work)
- Always clean/parse SQL response (remove markdown blocks)
- Handle errors gracefully (SQL generation or execution failures)
- Display all intermediate steps in UI (enhanced query, generated SQL)
```

---

## Tell Cursor This:
```
✅ Cortex is WORKING! Use real Cortex integration.

Configuration file: SNOWFLAKE_CONFIG.md has all details.

Key points:
1. Use CORTEX.COMPLETE with 'mistral-large' model
2. Provide schema context in the prompt
3. Clean the response (remove markdown blocks if present)
4. Execute generated SQL on SNOWFLAKE_SAMPLE_DATA.TPCH_SF1
5. Return results to UI

Complete cortex_client.py with real Cortex calls - no mock mode needed!
Follow the implementation examples in SNOWFLAKE_CONFIG.md.