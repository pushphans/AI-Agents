# Personal Finance Tracker Agent

An AI-powered conversational agent that helps you manage personal expenses through natural language. Built with **LangGraph**, **FastAPI**, and **OpenAI GPT-4o-mini** — it provides full CRUD operations on expense data stored in a local CSV file.

---

## Features

- **Add expenses** — Record new expenses with type, amount, item, and date
- **List all expenses** — View all recorded expenses in a formatted table
- **Look up by ID** — Retrieve details of a specific expense
- **Filter expenses** — Filter by date range, expense type, amount range, or item text
- **Update expenses** — Modify any field of an existing expense
- **Delete expenses** — Remove an expense record

All operations are thread-safe with atomic file writes to prevent data corruption.

---

## Architecture

```
User Request
    │
    ▼
┌──────────────────────────────┐
│   FastAPI Server             │  POST /api/v1/chat
│   (app/main.py)              │  - Pydantic validation
│   (app/api/router.py)        │  - Tenacity retry (3 attempts)
│                              │  - 30s timeout
│                              │  - Observability callback
└──────────┬───────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│   LangGraph ReAct Agent                │
│                                        │
│   ┌──────────┐                         │
│   │  Agent   │  GPT-4o-mini + 6 tools  │
│   │  Node    │  ─→ reply or tool call  │
│   └────┬─────┘                         │
│        │                               │
│   ┌────┴─────┐                         │
│   │  Tools   │  tools_condition        │
│   │  Node    │  routes tool calls      │
│   └────┬─────┘                         │
│        │  (loop back to Agent)         │
│        ▼                               │
│   ┌──────────┐                         │
│   │  Memory  │  Conversation history   │
│   └──────────┘                         │
└──────────┬─────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│   CSV Storage                │
│   (data/expenses.csv)        │
│                              │
│   - Thread-safe (Lock)       │
│   - Atomic writes (tmp+mv)   │
│   - Columns: id, date, type, │
│              amount, item    │
└──────────────────────────────┘
```

### Agent Loop

1. **System prompt** instructs the LLM on expense management, available tools, and current date
2. **LLM (GPT-4o-mini)** receives conversation history and decides:
   - Respond directly → route to **END**
   - Call a tool → route to **Tool Node**
3. **Tool Node** executes the expense operation against the CSV file
4. Results feed back to the LLM for natural-language synthesis
5. Cycle repeats until a final answer is produced

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Runtime |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| LangChain | LLM abstraction & tool framework |
| LangGraph | Agent state graph orchestration |
| OpenAI GPT-4o-mini | Language model |
| LangChain-OpenAI | OpenAI integration |
| Pydantic / Pydantic-Settings | Validation & configuration |
| LangSmith | LLM tracing & observability |
| Tenacity | Retry logic |
| threading (stdlib) | Thread-safe CSV access |
| csv (stdlib) | Expense data storage |
| pytest | Testing |
| uv | Package manager |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key

### Installation

```bash
# Clone and enter the project
cd A1.2-Personal-Finance-Tracker-Agent

# Create virtual environment and install dependencies
uv venv
uv sync

# Or with pip:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-openai-key

# Optional: LangSmith tracing
LANGSMITH_API_KEY=lsv2_your-langsmith-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=A1.2-Personal-Finance-Tracker-Agent
```

### Run the Server

```bash
uvicorn app.main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`.

---

## API Reference

### `POST /api/v1/chat`

Send a message to the agent and receive a response.

**Request body:**

```json
{
  "message": "How much did I spend on food this month?"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Natural language request (required, min 1 char) |

**Response body:**

```json
{
  "response": "You spent $500.00 on Food in June 2026."
}
```

---

## Tools

Each tool has a Pydantic schema for input validation.

| Tool | Input Schema | Description |
|------|-------------|-------------|
| `create_expense` | `CreateExpenseSchema` | Add expense (type, amount, item, optional date) |
| `list_expenses` | — | Return all expenses as a formatted table |
| `get_expense_by_id` | `GetExpenseByIdSchema` | Look up a single expense by ID |
| `update_expense` | `UpdateExpenseSchema` | Partial update (only non-None fields are changed) |
| `filter_expenses` | `FilterExpensesSchema` | Filter by date range, type, amount range, item text |
| `delete_expense` | `DeleteExpenseSchema` | Remove an expense by ID |

### Input Validation Rules

| Field | Constraints |
|-------|-------------|
| `amount` | Must be positive (> 0) |
| `date` | Must match `YYYY-MM-DD` format |
| `expense_type` | 1–50 characters |
| `item` | 1–200 characters |
| `expense_id` | Must be positive integer |

---

## Data Storage

Expenses are stored in `data/expenses.csv`.

### Schema

| Column | Type | Example |
|--------|------|---------|
| `id` | Integer | `1` |
| `date` | String (YYYY-MM-DD) | `2026-06-07` |
| `expense_type` | String | `Food` |
| `amount` | Decimal | `500.00` |
| `item` | String | `Groceries` |

### Design Features

- **Thread-safe** — All reads and writes are protected by a `threading.Lock`
- **Atomic writes** — Data is written to a `.tmp` file first, then atomically renamed via `os.replace()`
- **Auto-creation** — The `data/` directory and CSV are created automatically if missing
- **Sample data** — Pre-populated with 3 example records for testing

---

## Project Structure

```
A1.2-Personal-Finance-Tracker-Agent/
├── .env                         # Environment variables (excluded from VCS)
├── .gitignore
├── .python-version              # Python 3.12
├── pyproject.toml               # Project metadata & dependencies
├── requirements.txt             # Pip dependencies
├── uv.lock                      # Lock file
├── README.md
├── data/
│   └── expenses.csv             # CSV-backed expense storage
└── app/
    ├── __init__.py
    ├── main.py                  # FastAPI application entry point
    ├── api/
    │   └── router.py            # FastAPI router (POST /api/v1/chat)
    ├── agent/
    │   └── personal_finance_agent.py  # LangGraph agent definition
    ├── schema/
    │   ├── __init__.py
    │   └── agent_schema.py      # Pydantic request/response models
    └── core/
        ├── __init__.py
        ├── config.py            # Pydantic settings from .env
        ├── exceptions.py        # (placeholder for custom exceptions)
        ├── observability.py     # LangChain callback for monitoring
        ├── state.py             # LangGraph AgentState schema
        └── tools.py             # All CRUD tools (CSV-backed)
```

---

## Running Tests

The project includes extensive test coverage (~915 lines).

```bash
# Run all tests
uv run pytest -v

# Run specific test files
uv run pytest tests/test_tools.py -v
uv run pytest tests/test_router.py -v
uv run pytest tests/test_edge_cases.py -v
```

### Test Coverage

| Test File | What It Tests |
|-----------|---------------|
| `test_schema.py` | Pydantic input validation (boundary cases, invalid input, extra fields) |
| `test_tools.py` | CRUD operations, edge cases, concurrent access, corrupted data |
| `test_agent.py` | Agent workflow compilation, LLM binding, error handling |
| `test_router.py` | API endpoint behavior (valid, invalid, missing, wrong method) |
| `test_edge_cases.py` | Filesystem errors, input boundaries, concurrency, data corruption |

### Test Fixtures

- `conftest.py` provides automatic CSV backup/restore before/after each test
- Tests run against the actual CSV file (isolated per test)

---

## Error Handling

| Scenario | HTTP Status | Behavior |
|----------|-------------|----------|
| Valid request | `200` | Returns agent response |
| Empty message | `422` | Pydantic validation error |
| Agent timeout (30s) | `504` | Tenacity retries up to 3 times |
| Transient failure | `503` | After retries exhausted |
| Unexpected error | `500` | Logged with traceback |
| Pydantic validation error | `422` | Detailed error messages |

---

## Observability

A custom `ObservabilityCallback` (LangChain `BaseCallbackHandler`) is attached to each request, tracking:

- **LLM calls** — Model name, latency, token usage (prompt/completion/total), estimated cost
- **Tool calls** — Tool name, latency
- **Request timing** — Start/end time, total duration
- **Errors** — Any exceptions during agent execution

Cost is calculated using per-model pricing ($0.00015/K input, $0.0006/K output for GPT-4o-mini).

---

## Example Conversations

```
User:   Add a food expense of $25 for lunch today
Agent:  Added expense: Food - $25.00 (Lunch) on 2026-06-10

User:   How much did I spend on fuel last week?
Agent:  You spent $50.00 on Fuel between June 3 and June 10.

User:   Show me all my expenses
Agent:  | ID | Date       | Type     | Amount  | Item   |
        |----|------------|----------|---------|--------|
        | 1  | 2026-06-07 | Clothing | $1000.00| Purchase
        | 2  | 2026-06-06 | Food     | $500.00 | Groceries
        | 3  | 2026-06-08 | Fuel     | $500.00 | Petrol
        | 4  | 2026-06-10 | Food     | $25.00  | Lunch

User:   Delete expense #2
Agent:  Expense #2 (Food - $500.00) has been deleted.
```
