# SQL Query Validator Agent

> A reflection-based AI agent that converts natural language to validated SQL queries using a Generator-Critic loop with production safety checks.

---

## What It Does

```
User: "Show me users who signed up last month"
        │
        ▼
   ┌─────────┐     ┌─────────┐     ┌──────────┐
   │Generator │────▶│ Critic  │────▶│ Executor │
   │(LLM)     │◀────│(LLM)    │     │(Python)  │
   └─────────┘     └─────────┘     └──────────┘
        ▲               │
        └─── fix ───────┘
            (max 3 iterations)
```

1. **Generator** converts your question into a SQL query
2. **Critic** validates the query against 7 production safety checks
3. If issues found, **Generator fixes** and loop repeats (max 3 iterations)
4. **Executor** runs the final validated query on SQLite and returns results

---

## 7 Validation Checks

| # | Check | What It Catches |
|---|-------|-----------------|
| 1 | Syntax | Malformed SQL |
| 2 | Schema Match | Non-existent tables/columns |
| 3 | JOIN Logic | Missing ON conditions, wrong join types |
| 4 | WHERE Safety | Always-true bypass (`WHERE 1=1`), missing filters |
| 5 | LIMIT Present | Unbounded result sets |
| 6 | Injection Safe | Raw string concatenation, unsafe patterns |
| 7 | Performance | Missing index usage on filtered/joined columns |

---

## Project Structure

```
A3.1-SQL-Query-Validator-Agent/
├── main.py                  # Entry point - runs uvicorn server
├── requirements.txt         # Python dependencies
├── .env                     # API keys (not committed)
├── .gitignore               # Excludes data.db, .venv, .env
│
└── app/
    ├── main.py              # FastAPI app initialization
    │
    ├── core/
    │   ├── config.py        # Settings, env vars, LangSmith config
    │   ├── database.py      # SQLite setup, schema, seed data, indexes
    │   └── state.py         # AgentState TypedDict definition
    │
    ├── agent/
    │   └── workflow.py      # LangGraph workflow - all nodes + graph
    │
    └── api/
        └── routes.py        # FastAPI endpoints (/setup, /validate)
```

---

## Tech Stack

- **Agent Framework:** LangGraph (StateGraph with conditional edges)
- **LLM:** DeepSeek Chat (via langchain-deepseek)
- **API:** FastAPI + Uvicorn
- **Database:** SQLite (file-based, auto-created)
- **Observability:** LangSmith (tracing + monitoring)
- **Structured Output:** Pydantic + `with_structured_output()` for Critic

---

## Setup

### 1. Clone & Install

```bash
git clone <repo-url>
cd A3.1-SQL-Query-Validator-Agent
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=A3.1-SQL Query Validator Agent
```

### 3. Run

```bash
python main.py
```

Server starts at `http://localhost:8000`

---

## API Endpoints

### `POST /setup`

Creates/resets the database with seed data. Run this first.

```bash
curl -X POST http://localhost:8000/setup
```

**Response:**
```json
{
    "message": "Database created successfully with seed data",
    "db_path": "C:/.../data.db",
    "tables": ["users", "orders", "products"]
}
```

### `POST /validate`

Send a natural language question, get validated SQL + results.

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all orders with user names"}'
```

**Response:**
```json
{
    "sql": "SELECT orders.id, orders.product_name, users.name AS user_name FROM orders INNER JOIN users ON orders.user_id = users.id LIMIT 10",
    "evaluation": "pass",
    "iterations": 0,
    "results": [
        {"id": 1, "product_name": "Laptop", "user_name": "Amit Sharma"},
        {"id": 2, "product_name": "Mouse", "user_name": "Amit Sharma"}
    ],
    "error": null
}
```

### Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## Database

Auto-created SQLite file (`data.db`) with 3 tables:

| Table | Rows | Description |
|-------|------|-------------|
| `users` | 10 | User profiles with signup dates |
| `orders` | 15 | Product orders with status tracking |
| `products` | 8 | Product catalog with categories |

Includes 6 indexes for optimized query performance. Database is recreated on each `/setup` call to ensure clean state.

---

## How the Reflection Loop Works

```
Iteration 1:
  Generator  → SELECT * FROM users
  Critic     → FAIL: Missing LIMIT, SELECT * not allowed
  Feedback   → ["Add LIMIT clause", "Specify columns"]

Iteration 2:
  Generator  → SELECT id, name, email FROM users WHERE is_active = 1 LIMIT 10
  Critic     → PASS
  Executor   → [{id: 1, name: "Amit Sharma", ...}, ...]
```

---

## Tracing with LangSmith

All LLM calls are automatically traced to LangSmith. View your project dashboard at:

```
https://smith.langchain.com/projects/A3.1-SQL Query Validator Agent
```

Traces include:
- Generator prompts and responses
- Critic validation results
- Iteration counts and feedback history

---

## Sample Questions

| Question | Expected Behavior |
|----------|-------------------|
| "How many users are active?" | `SELECT COUNT(*) FROM users WHERE is_active = 1 LIMIT 1` |
| "Show me users who signed up last month" | Date range filter on `signup_date` |
| "Top 3 users by total spending" | JOIN + aggregation + ORDER BY + LIMIT |
| "What orders are pending?" | Filter on `status` column |
| "Show all products in Electronics" | Filter on `category` column |

---

## License

MIT
