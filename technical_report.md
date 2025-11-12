# NL-SQL Assistant Alpha - Technical Documentation

## 1. Project Overview & Philosophy

### Problem Statement
Business users need to query Snowflake databases but lack SQL expertise. Traditional BI tools require learning query languages or building dashboards. This project enables natural language questions to be automatically converted to SQL and executed.

---

## 2. Architecture & System Design

### High-Level Architecture

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ Natural Language Query
       ▼
┌─────────────────────────────────────┐
│         Streamlit UI (app.py)       │
│  - Text input                        │
│  - Display: enhanced query, SQL,     │
│    results                           │
└──────┬───────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Orchestrator (orchestrator.py) │
│  - Coordinates linear flow           │
│  - No business logic                 │
└──────┬───────────────────────────────┘
       │
       ├─────────────────┐
       ▼                 ▼
┌──────────────┐  ┌──────────────────────┐
│ Query        │  │ Cortex Client        │
│ Enhancer     │  │ (cortex_client.py)   │
│              │  │                      │
│ - Normalize  │  │ - Build prompt       │
│ - Expand     │  │ - Call Cortex API    │
│ - Add date   │  │ - Clean SQL response │
│              │  │ - Execute SQL        │
└──────────────┘  └──────┬───────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Snowflake  │
                  │   Database   │
                  └──────────────┘
```

### Component Relationships

**Data Flow:**
1. `app.py` captures user input
2. `orchestrator.py` calls `query_enhancer.py` → returns enhanced string
3. `orchestrator.py` passes enhanced query to `cortex_client.py`
4. `cortex_client.py` builds prompt, calls Cortex API, executes SQL
5. Results flow back: `cortex_client` → `orchestrator` → `app.py` → UI

**Dependency Graph:**
```
app.py
  └─> orchestrator.py
        ├─> query_enhancer.py (no dependencies)
        ├─> cortex_client.py
        │     └─> config.py
        └─> config.py
```

### Directory Structure

```
final_project_alpha_v/
├── app.py                 # Streamlit UI - entry point
├── orchestrator.py        # Linear flow coordinator
├── query_enhancer.py      # Deterministic text preprocessing
├── cortex_client.py       # Snowflake Cortex API wrapper
├── config.py              # Environment variable loader
├── requirements.txt        # Python dependencies
├── README.md              # Setup instructions
├── plan.md                # Original design document
└── SNOWFLAKE_CONFIG.md    # Cortex integration details
```

**Purpose of Each File:**
- **app.py**: Pure UI layer. Handles Streamlit widgets, displays results, catches exceptions.
- **orchestrator.py**: Thin coordinator. Calls enhancer and client, assembles response dict. No business logic.
- **query_enhancer.py**: Stateless text transformation. Normalizes, expands abbreviations, adds date context.
- **cortex_client.py**: Integration layer. Manages Snowflake connection, builds prompts, invokes Cortex, executes SQL.
- **config.py**: Configuration loader. Validates environment variables, returns typed Settings object.

### Entry Points

**Main Execution Path:**
```python
# Entry: streamlit run app.py
app.py::main()
  └─> Orchestrator.from_env()  # Factory method loads config
       └─> Orchestrator.run(user_query)
            ├─> enhance_query(user_query)  # query_enhancer.py
            └─> cortex_client.generate_sql_and_results(enhanced)
                 ├─> _build_prompt()
                 ├─> _build_cortex_statement()
                 ├─> _invoke_cortex()  # Calls SNOWFLAKE.CORTEX.COMPLETE
                 ├─> _clean_sql()
                 └─> _execute_sql()
```

### State Management

**No persistent state.** Each request is stateless:
- No session storage
- No conversation history
- No caching
- Streamlit's `st.session_state` is unused

This simplifies the architecture but means users can't ask follow-up questions like "show me more details" or "filter that by date."

### API Design Patterns

**Factory Pattern:**
```python
Orchestrator.from_env()  # Loads config, creates client, returns instance
```

**Context Manager Pattern:**
```python
@contextmanager
def _connection(self) -> Iterator[SnowflakeConnection]:
    # Ensures connection cleanup
```

**Error Propagation:**
- Custom exception: `CortexClientError` (domain-specific)
- Re-raised from `orchestrator.py` to `app.py` for UI display
- No error swallowing

---

## 3. Technical Stack

### Core Frameworks & Libraries

| Library | Version | Purpose | Why Chosen |
|---------|---------|---------|------------|
| **streamlit** | 1.28.0 | UI framework | Fastest way to build Python web UIs. No HTML/CSS/JS needed. |
| **snowflake-connector-python** | 3.5.0 | Database driver | Official Snowflake Python connector. Required for Cortex API calls. |
| **snowflake-snowpark-python** | 1.11.0 | Snowpark API | Listed but **not used** in code. Likely included for future expansion. |
| **python-dotenv** | 1.0.0 | Environment loader | Standard way to load `.env` files. Keeps secrets out of code. |
| **pydantic** | 2.5.0 | Data validation | Validates environment variables, provides type safety for Settings. |

### Key Dependencies Breakdown

**streamlit**: Handles HTTP server, WebSocket for reactivity, widget rendering. Zero configuration needed.

**snowflake-connector-python**: Provides `snowflake.connector.connect()` and cursor API. Used for:
- Establishing connection (via `config.py` settings)
- Executing SQL (both Cortex calls and generated queries)
- Fetching results

**pydantic**: `Settings` class validates env vars at startup. Fails fast if missing/invalid values.

### Environment Configuration

**.env Structure:**
```bash
SNOWFLAKE_ACCOUNT=yqc42692.us-east-1
SNOWFLAKE_USER=ACCOUNTADMIN
SNOWFLAKE_PASSWORD=<secret>
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

**Loading Flow:**
1. `config.py::load_settings()` calls `load_dotenv()` (reads `.env`)
2. Extracts all `SNOWFLAKE_*` variables
3. Checks for missing values (raises `RuntimeError` if any missing)
4. Creates `Settings` Pydantic model (validates types)
5. Returns `Settings` object with `.as_connection_kwargs()` method

**Why This Approach:**
- Fail fast: Missing env vars cause immediate error (better than runtime failures)
- Type safety: Pydantic ensures correct types
- No hardcoded secrets: All credentials externalized

### Build & Deployment Pipeline

**No build step.** Python interpreted directly.

**Deployment:**
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` file
3. Run: `streamlit run app.py`
4. Access: `http://localhost:8501` (default Streamlit port)

**No CI/CD, no containerization, no production deployment.** This is alpha-only.

---

## 4. Critical Code Sections

### 4.1 Cortex API Integration (`cortex_client.py::generate_sql_and_results`)

**Why Critical:** This is the core GenAI integration. Everything else is plumbing.

```31:53:cortex_client.py
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
```

**Key Design Decisions:**
- **Single connection context**: Opens connection once, uses for both Cortex call and SQL execution
- **Error wrapping**: Converts `ProgrammingError` to domain-specific `CortexClientError`
- **Row dict conversion**: Converts tuples to dicts for easier UI consumption

### 4.2 Prompt Engineering (`cortex_client.py::_build_prompt`)

**Why Critical:** Prompt structure determines SQL quality. This is where the "magic" happens.

```55:69:cortex_client.py
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
```

**Prompt Strategy:**
- **Role assignment**: "You are a SQL expert" sets context
- **Schema injection**: Hardcoded table schemas (alpha limitation - should be dynamic in production)
- **Output format constraint**: "ONLY the SQL query" prevents markdown blocks
- **Why it works**: Mistral-large follows instructions well, schema context enables accurate column mapping

### 4.3 SQL Response Cleaning (`cortex_client.py::_clean_sql`)

**Why Critical:** LLMs often wrap SQL in markdown. This ensures executable SQL.

```90:94:cortex_client.py
    def _clean_sql(self, raw_sql: str) -> str:
        cleaned = raw_sql.strip()
        for marker in ("```sql", "```", ";"):
            cleaned = cleaned.replace(marker, "")
        return cleaned.strip()
```

**Why This Approach:**
- **Simple string replacement**: Fast, deterministic
- **Removes common markdown**: ````sql` blocks, trailing semicolons
- **Trade-off**: Doesn't handle edge cases (e.g., SQL containing "```" as data), but sufficient for alpha

### 4.4 Query Enhancement (`query_enhancer.py::enhance_query`)

**Why Critical:** Adds context that improves SQL generation accuracy.

```14:35:query_enhancer.py
def enhance_query(query: str, today: date | None = None) -> str:
    """
    Apply lightweight, deterministic enhancements to the user's question.
    - Normalize whitespace
    - Lowercase the text
    - Expand a small set of abbreviations
    - Add the current date for context
    """
    normalized = query.strip()
    today = today or date.today()

    lowered = normalized.lower()
    tokens = lowered.split()
    expanded_tokens = [ABBREVIATIONS.get(token, token) for token in tokens]
    expanded = " ".join(expanded_tokens)

    if expanded:
        contextualized = f"{expanded}. Assume current date is {today.isoformat()}."
    else:
        contextualized = f"Assume current date is {today.isoformat()}."

    return contextualized
```

**Enhancement Strategy:**
- **Normalization**: Lowercase ensures consistent abbreviation matching
- **Abbreviation expansion**: Small dictionary (`rev` → `revenue`) helps LLM understand domain terms
- **Date injection**: Enables relative date queries ("recent orders" becomes "orders after 2024-01-15")
- **Why deterministic**: No LLM calls = fast, predictable, no API costs

### 4.5 Connection Management (`cortex_client.py::_connection`)

**Why Critical:** Ensures resources are cleaned up, prevents connection leaks.

```21:29:cortex_client.py
    @contextmanager
    def _connection(self) -> Iterator[SnowflakeConnection]:
        connection = snowflake.connector.connect(
            **self._settings.as_connection_kwargs()
        )
        try:
            yield connection
        finally:
            connection.close()
```

**Design Pattern:**
- **Context manager**: Guarantees `close()` is called even if exceptions occur
- **Reused connection**: Same connection used for Cortex call and SQL execution (efficient)
- **Why not connection pooling**: Alpha doesn't need it. One request at a time.

### 4.6 Error Handling Flow (`app.py::main`)

**Why Critical:** User experience depends on clear error messages.

```21:34:app.py
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
```

**Error Handling Strategy:**
- **Layered exceptions**: Configuration errors vs. Cortex errors vs. unexpected errors
- **Early returns**: Prevents partial UI rendering on errors
- **User-friendly messages**: `st.error()` displays prominently in Streamlit UI
- **Why no retries**: Alpha simplicity. Production would add retry logic.

### 4.7 Orchestrator Pattern (`orchestrator.py::run`)

**Why Critical:** This is the "glue" that coordinates the entire flow.

```20:35:orchestrator.py
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
        }
```

**Design Decisions:**
- **Thin layer**: No business logic, just coordination
- **Exception propagation**: Re-raises `CortexClientError` (lets UI handle it)
- **Response assembly**: Combines enhanced query + SQL + results for UI display
- **Why this structure**: Makes testing easier (can mock `cortex_client`), keeps UI decoupled

---

## 5. Workflows & Data Flow

### User Request Journey

**Step-by-Step Flow:**

1. **User Input** (`app.py`)
   - User types: "How many orders are there?"
   - Clicks "Run Query" button
   - `app.py` captures `query_input` string

2. **Orchestration** (`orchestrator.py`)
   - `Orchestrator.from_env()` loads config, creates `CortexClient`
   - `orchestrator.run(query_input)` called

3. **Query Enhancement** (`query_enhancer.py`)
   - Input: `"How many orders are there?"`
   - Process: lowercase → tokenize → expand abbreviations → add date
   - Output: `"how many orders are there?. Assume current date is 2024-01-15."`

4. **Cortex Integration** (`cortex_client.py`)
   - **Prompt Building**: Schema + enhanced query → full prompt string
   - **Cortex Call**: `SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large', prompt)`
   - **SQL Cleaning**: Remove markdown, extract SQL
   - **SQL Execution**: Execute cleaned SQL on Snowflake
   - **Result Fetching**: Get rows + column names

5. **Response Assembly** (`orchestrator.py`)
   - Combines: `{enhanced_query, generated_sql, rows}`
   - Returns dict to `app.py`

6. **UI Display** (`app.py`)
   - Shows enhanced query in code block
   - Shows generated SQL in syntax-highlighted code block
   - Shows results in Streamlit dataframe

### Database Interactions

**Connection Lifecycle:**
```
1. User clicks "Run Query"
2. cortex_client._connection() context manager opens connection
3. Connection used for:
   a. Cortex API call (SELECT SNOWFLAKE.CORTEX.COMPLETE(...))
   b. Generated SQL execution (SELECT COUNT(*) FROM ORDERS)
4. Context manager closes connection (finally block)
```

**Why Single Connection:**
- Efficient: Reuses connection for both operations
- Simple: No connection pooling complexity
- Sufficient: Alpha handles one request at a time

### External API Integration

**Snowflake Cortex API:**

**Endpoint:** `SNOWFLAKE.CORTEX.COMPLETE(model, prompt)`

**Implementation:**
```71:78:cortex_client.py
    def _build_cortex_statement(self, prompt: str) -> str:
        escaped_prompt = prompt.replace("'", "''")
        return (
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(\n"
            "    'mistral-large',\n"
            "    f'{escaped_prompt}'\n"
            ") AS generated_sql"
        )
```

**Key Details:**
- **Model**: `mistral-large` (hardcoded, proven to work)
- **SQL injection prevention**: Escapes single quotes (`'` → `''`)
- **Response format**: Returns string containing SQL (may include markdown)
- **Why SQL-based API**: No REST endpoints. Cortex is a SQL function, called via standard Snowflake connector.

### Error Handling Patterns

**Three-Layer Error Handling:**

1. **Configuration Errors** (`config.py`)
   - Missing env vars → `RuntimeError` with list of missing vars
   - Invalid types → Pydantic `ValidationError` wrapped in `RuntimeError`

2. **Cortex Errors** (`cortex_client.py`)
   - Empty Cortex response → `CortexClientError("Cortex Analyst returned an empty response.")`
   - SQL execution failure → `ProgrammingError` wrapped in `CortexClientError`
   - No SQL generated → `CortexClientError("Cortex Analyst did not provide a SQL statement.")`

3. **UI Errors** (`app.py`)
   - Catches `RuntimeError` (config) → shows "Configuration error"
   - Catches `CortexClientError` → shows "Cortex error"
   - Catches `Exception` → shows "Unexpected error" (catch-all)

**Error Propagation:**
```
Snowflake ProgrammingError
  → CortexClientError (wrapped)
    → Re-raised from orchestrator
      → Caught in app.py
        → Displayed via st.error()
```

### Logging and Monitoring

**Current State: None.**

**Why:** Alpha simplicity. No logging framework, no monitoring, no metrics.

**Production Would Need:**
- Request logging (user query, generated SQL, execution time)
- Error logging (stack traces, context)
- Performance metrics (Cortex latency, SQL execution time)
- Usage analytics (query patterns, success rates)

---

## 6. GenAI-Specific Elements

### LLM Integration Points

**Single Integration: Snowflake Cortex COMPLETE**

**Model:** `mistral-large`
- **Why this model**: Proven to work with Snowflake Cortex, good SQL generation
- **Alternative models**: Could use `llama3-70b` or `llama3-8b`, but `mistral-large` tested and working

**Integration Method:**
```80:88:cortex_client.py
    def _invoke_cortex(self, connection: SnowflakeConnection, cortex_sql: str) -> str:
        with connection.cursor() as cursor:
            cursor.execute(cortex_sql)
            result = cursor.fetchone()

        if not result or not result[0]:
            raise CortexClientError("Cortex Analyst returned an empty response.")

        return str(result[0])
```

**Why SQL Function vs. REST API:**
- **Native integration**: No API keys, uses Snowflake authentication
- **Simpler**: Standard SQL cursor, no HTTP client needed
- **Cost**: Billed through Snowflake account (no separate API billing)

### Prompt Engineering Strategies

**Prompt Structure:**
1. **Role Assignment**: "You are a SQL expert for Snowflake"
   - Sets context, improves instruction following

2. **Schema Injection**: Hardcoded table schemas
   - Enables accurate column mapping
   - **Alpha limitation**: Should be dynamic (query `INFORMATION_SCHEMA`)

3. **Output Format Constraint**: "Generate ONLY the SQL query. No explanation, no markdown"
   - Prevents verbose responses
   - Reduces need for complex parsing

4. **Enhanced Query Injection**: User query + date context
   - Provides full context for SQL generation

**Prompt Template:**
```
Role: SQL expert
Schema: [hardcoded tables with columns]
User question: [enhanced query with date]
Constraint: SQL only, no markdown
```

**Why This Works:**
- **Clear instructions**: LLM knows exactly what to output
- **Schema context**: Enables accurate SQL generation without table discovery
- **Format constraint**: Reduces post-processing complexity

### Token Management and Optimization

**Current State: No explicit token management.**

**Token Usage:**
- **Input tokens**: ~150-200 tokens per request (prompt + schema)
- **Output tokens**: ~50-100 tokens (SQL query)
- **Total**: ~200-300 tokens per request

**Optimization Opportunities (Not in Alpha):**
- **Schema caching**: Don't include full schema if unchanged
- **Prompt compression**: Use shorter schema descriptions
- **Response caching**: Cache SQL for identical queries

**Why Not Optimized:**
- Alpha doesn't need it (low volume)
- Simplicity > optimization
- Can add later if needed

### Embedding/Vector Operations

**None.** This is a direct LLM call, not RAG.

**Why No RAG:**
- **Single database**: No need to search across multiple sources
- **Schema is small**: Can fit in prompt (3 tables, ~15 columns)
- **Alpha simplicity**: RAG adds complexity (vector DB, embeddings, retrieval)

**When RAG Would Help:**
- Large schemas (100+ tables)
- Dynamic schema discovery
- Query history retrieval ("similar queries")

### RAG Patterns or Fine-Tuning

**None.** This is zero-shot SQL generation.

**Why Zero-Shot:**
- **Cortex models are pre-trained**: Mistral-large already knows SQL
- **Schema in prompt**: Provides all needed context
- **No fine-tuning needed**: Model performs well with good prompts

**When Fine-Tuning Would Help:**
- Domain-specific SQL patterns (e.g., financial calculations)
- Custom business logic
- Consistent formatting requirements

---

## 7. Key Implementation Details

### SQL Injection Prevention

**Current Approach:**
```71:78:cortex_client.py
    def _build_cortex_statement(self, prompt: str) -> str:
        escaped_prompt = prompt.replace("'", "''")
        return (
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(\n"
            "    'mistral-large',\n"
            "    f'{escaped_prompt}'\n"
            ") AS generated_sql"
        )
```

**Why This Works:**
- Escapes single quotes in prompt (prevents breaking SQL string)
- **Limitation**: Doesn't use parameterized queries (Cortex API is string-based)
- **Risk**: Low (user input goes to LLM, not directly to SQL execution)

**Generated SQL Execution:**
- Generated SQL is executed directly (no parameterization)
- **Risk**: If LLM generates malicious SQL, it could execute
- **Mitigation**: Run with least-privilege Snowflake user (not implemented in alpha)

### Connection Security

**Authentication:** Username/password from `.env` file

**Why Not OAuth/SSO:**
- Alpha simplicity
- `.env` file should be in `.gitignore` (not committed)

**Production Would Need:**
- OAuth/SSO integration
- Connection pooling with authentication refresh
- Secrets management (AWS Secrets Manager, Azure Key Vault)

### Performance Characteristics

**Latency Breakdown (Estimated):**
- Query enhancement: <1ms (string operations)
- Cortex API call: 2-5 seconds (LLM inference)
- SQL execution: 100ms-2s (depends on query complexity)
- **Total**: 2-7 seconds per request

**Bottlenecks:**
- **Cortex API**: LLM inference is slowest step
- **SQL execution**: Can be slow for complex queries (not optimized in alpha)

**Why No Async:**
- Streamlit is synchronous
- Alpha doesn't need concurrent requests
- Simpler code

---

## 8. Testing & Validation

### Current Testing State

**None.** No unit tests, no integration tests.

### Manual Testing Approach

**Test Queries (from SNOWFLAKE_CONFIG.md):**
1. "How many orders are there?" → `SELECT COUNT(*) FROM ORDERS`
2. "What is the total revenue?" → `SELECT SUM(O_TOTALPRICE) FROM ORDERS`
3. "How many customers do we have?" → `SELECT COUNT(DISTINCT C_CUSTKEY) FROM CUSTOMER`
4. "Show me orders from 1995" → `SELECT * FROM ORDERS WHERE YEAR(O_ORDERDATE) = 1995`

### Validation Strategy

**Manual Verification:**
- Check enhanced query makes sense
- Verify generated SQL is syntactically correct
- Confirm results match expected values
- Test error cases (empty query, invalid SQL generation)

---

## 9. Future Expansion Points

### What's NOT in Alpha (By Design)

- **Group 2 Integration**: Reasoning detection, multi-step queries
- **Conversation History**: Can't ask follow-ups
- **Dynamic Schema Discovery**: Schema is hardcoded
- **Caching**: Every query hits Cortex API
- **Advanced Error Recovery**: No retries, no fallbacks
- **User Authentication**: No login, no user management
- **Query History**: No saved queries, no favorites

### Easy Expansion Points

**Low-Hanging Fruit:**
1. **Multiple Models**: Add dropdown to select `mistral-large` vs `llama3-70b`
2. **Query History**: Store last N queries in `st.session_state`
3. **Export Results**: Add "Download CSV" button
4. **Better Error Messages**: Parse Snowflake errors, show user-friendly messages

**Medium Complexity:**
1. **Dynamic Schema**: Query `INFORMATION_SCHEMA` to build prompt
2. **Query Validation**: Check SQL before execution (syntax, permissions)
3. **Result Pagination**: Handle large result sets

**High Complexity:**
1. **RAG Integration**: Vector DB for query history, schema documentation
2. **Multi-Database Support**: Switch between databases
3. **Conversation Context**: Maintain context across multiple queries

---

## 10. Summary: What Makes This Work

### Core Innovation

**Direct LLM-to-SQL Pipeline**: No intermediate steps, no complex orchestration. User question → Enhanced prompt → Cortex API → SQL execution → Results.

### Why It's Simple

1. **Single LLM Provider**: Snowflake Cortex (no API key management)
2. **Linear Flow**: No loops, no state machines
3. **Stateless**: Each request is independent
4. **Thin Layers**: Each component does one thing
5. **Fail Fast**: Clear errors, no silent failures

### Why It Works

1. **Good Prompt Engineering**: Schema + clear instructions = accurate SQL
2. **Model Quality**: Mistral-large generates correct SQL for simple queries
3. **Simple Domain**: TPCH sample data is well-structured, predictable
4. **Clear Constraints**: "SQL only" prevents verbose responses

### Key Takeaways

1. **Prompt structure matters more than model selection** (for this use case)
2. **Schema context is critical** for accurate SQL generation
3. **Simple string operations** can enhance queries effectively (no need for LLM-based enhancement in alpha)
4. **Native integrations** (Cortex as SQL function) are simpler than REST APIs
5. **Show intermediate steps** (enhanced query, SQL) builds user trust

---

