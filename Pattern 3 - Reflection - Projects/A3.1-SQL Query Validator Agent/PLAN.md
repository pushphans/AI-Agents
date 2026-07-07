# SQL Query Validator Agent - Implementation Plan

## Architecture Overview

```
User Input (Natural Language)
        │
        ▼
┌─────────────────┐
│  1. Generator    │  ── Natural Language → SQL Query
│     Node         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Critic       │  ── Validates SQL (7 checks)
│     Node         │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Issue?  │
    └────┬────┘
    Yes  │  No
    │    │
    ▼    │
Generator──┘  (max 3 iterations)
    │
    ▼
┌─────────────────┐
│  3. Executor     │  ── Runs final SQL on SQLite DB
│     Node         │
└────────┬────────┘
         │
         ▼
   Final Result
```

---

## Nodes to Build (3 Nodes)

### Node 1: Generator Node
- **Input:** Natural language question + schema context (and previous feedback if re-iterating)
- **Output:** SQL query string
- **Responsibility:** Convert user's natural language into a valid SQL query
- **LLM Prompt:** "Given this database schema, write a SQL query for: {user_question}"

### Node 2: Critic Node
- **Input:** SQL query + schema context
- **Output:** Validation result (pass/fail) + list of issues + severity
- **Responsibility:** Check SQL on 7 parameters
- **7 Validation Checks:**
  1. **Syntax Correct?** - Is the SQL syntactically valid?
  2. **Tables/Columns Exist?** - Do referenced tables and columns match the schema?
  3. **JOIN Logic Sahi Hai?** - Are JOINs correct (right join type, correct ON condition)?
  4. **WHERE Clause Safe Hai?** - No dangerous conditions (e.g., `WHERE 1=1` bypass, missing filters on large tables)
  5. **LIMIT Lagaya?** - Does the query have a LIMIT clause to prevent massive result sets?
  6. **Injection Risk?** - Any raw string concatenation or unsafe patterns?
  7. **Performance: Index Use?** - Does the query leverage indexed columns for WHERE/JOIN?

### Node 3: Executor Node
- **Input:** Validated SQL query
- **Output:** Query results (rows + column names)
- **Responsibility:** Execute the final validated SQL on the SQLite database and return results

---

## State / Data Passing

```python
class AgentState(TypedDict):
    user_question: str
    current_sql: str
    iteration: int
    max_iterations: int
    validation_result: dict
    is_valid: bool
    feedback: str
    query_results: list[dict]
    error: str | None
```

---

## Database Approach: Option B - File DB (Auto-Create)

- **DB file:** `data.db` (created in project root on first run)
- **Auto-create:** Pehli baar `python main.py` chalao toh tables + seed data automatically banti hai
- **Reuse:** Doosri baar chalane pe existing `data.db` file re-use hoti hai - seed data dobara nahi banta
- **Zero setup:** Koi alag se SQL install ya config nahi - bas clone karo aur chalao
- **`.gitignore`:** `data.db` file ko `.gitignore` mein daalna hai taaki git mein commit na ho

---

## Database Schema (SQLite - Dummy Data)

### Table 1: `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT 1
);
```

**Dummy Data (10 rows):**
```sql
INSERT INTO users (name, email, signup_date, is_active) VALUES
('Amit Sharma', 'amit@example.com', '2026-01-15', 1),
('Priya Patel', 'priya@example.com', '2026-02-20', 1),
('Rahul Verma', 'rahul@example.com', '2026-03-10', 1),
('Sneha Gupta', 'sneha@example.com', '2026-04-05', 0),
('Vikram Singh', 'vikram@example.com', '2026-05-12', 1),
('Neha Joshi', 'neha@example.com', '2026-06-18', 1),
('Arjun Mehta', 'arjun@example.com', '2026-01-22', 1),
('Kavita Reddy', 'kavita@example.com', '2026-02-28', 0),
('Rohit Nair', 'rohit@example.com', '2026-03-15', 1),
('Ananya Das', 'ananya@example.com', '2026-04-30', 1);
```

### Table 2: `orders`
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    amount REAL NOT NULL,
    order_date DATE NOT NULL,
    status TEXT CHECK(status IN ('pending', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Dummy Data (15 rows):**
```sql
INSERT INTO orders (user_id, product_name, amount, order_date, status) VALUES
(1, 'Laptop', 54999.00, '2026-06-01', 'delivered'),
(1, 'Mouse', 799.00, '2026-06-15', 'delivered'),
(2, 'Keyboard', 2499.00, '2026-06-10', 'shipped'),
(2, 'Monitor', 18999.00, '2026-06-20', 'pending'),
(3, 'Headphones', 3499.00, '2026-06-05', 'delivered'),
(4, 'Webcam', 4999.00, '2026-06-12', 'cancelled'),
(5, 'Laptop', 62999.00, '2026-06-18', 'shipped'),
(6, 'Tablet', 29999.00, '2026-06-22', 'pending'),
(7, 'Phone Case', 599.00, '2026-06-25', 'delivered'),
(8, 'Charger', 1299.00, '2026-06-28', 'shipped'),
(9, 'Earbuds', 1999.00, '2026-07-01', 'pending'),
(10, 'Smartwatch', 14999.00, '2026-07-03', 'delivered'),
(3, 'USB Cable', 399.00, '2026-07-05', 'shipped'),
(1, 'Stand', 1899.00, '2026-07-06', 'pending'),
(5, 'Mousepad', 499.00, '2026-07-06', 'delivered');
```

### Table 3: `products`
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0
);
```

**Dummy Data (8 rows):**
```sql
INSERT INTO products (name, category, price, stock) VALUES
('Laptop', 'Electronics', 54999.00, 25),
('Mouse', 'Accessories', 799.00, 150),
('Keyboard', 'Accessories', 2499.00, 80),
('Monitor', 'Electronics', 18999.00, 40),
('Headphones', 'Audio', 3499.00, 60),
('Webcam', 'Electronics', 4999.00, 35),
('Tablet', 'Electronics', 29999.00, 20),
('Smartwatch', 'Wearables', 14999.00, 45);
```

---

## Indexes (for performance check in Critic)
```sql
CREATE INDEX idx_users_signup_date ON users(signup_date);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_products_category ON products(category);
```

---

## Critic Validation Rules (Detailed)

| # | Check | Pass Condition | Fail Example |
|---|-------|---------------|--------------|
| 1 | Syntax | SQL parses without error | Missing comma, wrong keyword |
| 2 | Schema Match | All tables/columns exist in DB | `SELECT phone FROM users` (no phone column) |
| 3 | JOIN Logic | Correct JOIN type + ON condition | `FROM users JOIN orders` without ON |
| 4 | WHERE Safety | No always-true bypass, has meaningful filter | `WHERE 1=1` or no WHERE at all on large table |
| 5 | LIMIT Present | Query has LIMIT clause | `SELECT * FROM orders` without LIMIT |
| 6 | Injection Safe | No raw string concat, uses parameterized patterns | `WHERE name = ' + user_input` |
| 7 | Performance | Uses indexed columns in WHERE/JOIN | `WHERE email = 'x'` (indexed) vs `WHERE name = 'x'` (not indexed) |

---

## Sample Test Cases

### Test Case 1: Simple Query (Should PASS on iteration 1)
```
Input:  "Show me users who signed up last month"
Expected SQL: SELECT id, name, email FROM users WHERE signup_date >= '2026-06-01' AND signup_date < '2026-07-01' LIMIT 10
```

### Test Case 2: JOIN Query (May need 1 fix)
```
Input:  "Show me all orders with user names"
Expected SQL: SELECT u.name, o.product_name, o.amount, o.status FROM orders o JOIN users u ON o.user_id = u.id LIMIT 10
```

### Test Case 3: Complex Query (Should need iteration)
```
Input:  "Top 3 users by total spending"
Expected SQL: SELECT u.name, SUM(o.amount) as total_spent FROM users u JOIN orders o ON u.id = o.user_id WHERE o.status != 'cancelled' GROUP BY u.id ORDER BY total_spent DESC LIMIT 3
```

### Test Case 4: Edge Case - Aggregation
```
Input:  "How many orders are pending?"
Expected SQL: SELECT COUNT(*) as pending_count FROM orders WHERE status = 'pending' LIMIT 1
```

### Test Case 5: Critic Catches Bad Query
```
Input:  "Show all users"
Bad SQL:  SELECT * FROM users
Critic Feedback: "Missing LIMIT clause. Add LIMIT to prevent large result sets."
Fixed SQL: SELECT id, name, email FROM users WHERE is_active = 1 LIMIT 10
```

---

## File Structure to Build

```
app/
├── agent/
│   ├── __init__.py
│   ├── graph.py          # LangGraph StateGraph - main workflow
│   ├── state.py          # AgentState TypedDict definition
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── generator.py  # Generator node - NL to SQL
│   │   ├── critic.py     # Critic node - 7-point validation
│   │   └── executor.py   # Executor node - run SQL on DB
│   └── prompts/
│       ├── __init__.py
│       ├── generator_prompt.py  # System prompt for Generator
│       └── critic_prompt.py     # System prompt for Critic
├── core/
│   ├── __init__.py
│   ├── database.py       # SQLite file DB auto-create, schema, seed data, indexes (Option B)
│   └── config.py         # Settings (model, max iterations, etc.)
├── api/
│   ├── __init__.py
│   └── routes.py         # FastAPI endpoints
main.py                   # Entry point
```

---

## Workflow Logic (graph.py)

```
START
  │
  ▼
[generator]  ─── generates SQL from user question
  │
  ▼
[critic]     ─── validates SQL on 7 checks
  │
  ├── is_valid == True AND iteration < max ──→ [executor] → END
  ├── is_valid == True AND iteration >= max ──→ [executor] → END
  └── is_valid == False ──→ iteration += 1
                              │
                              ├── iteration < max ──→ [generator] (with feedback)
                              └── iteration >= max ──→ [executor] (with best effort) → END
```

---

## API Endpoints

```
POST /validate
  Body: { "question": "Show me users who signed up last month" }
  Response: {
    "final_sql": "SELECT ...",
    "iterations": 2,
    "validation_log": [...],
    "results": [ { ... }, ... ]
  }

GET /schema
  Response: { "tables": { ... } }   # Returns current DB schema
```

---

## Clone & Play Experience

```bash
git clone <repo-url>
cd A3.1-SQL-Query-Validator-Agent
pip install -r requirements.txt
python main.py    # Pehli baar: data.db banti hai + seed data
python main.py    # Doosri baar: same data re-use hoti hai
```

**Zero setup - no SQL installation, no manual DB config, no seed scripts.**

---

## Implementation Order

| Step | Task | Files |
|------|------|-------|
| 1 | Add `data.db` to `.gitignore` | `.gitignore` |
| 2 | Set up database + seed data (auto-create) | `core/database.py` |
| 3 | Define state | `agent/state.py` |
| 4 | Build Generator node + prompt | `agent/nodes/generator.py`, `agent/prompts/generator_prompt.py` |
| 5 | Build Critic node + prompt | `agent/nodes/critic.py`, `agent/prompts/critic_prompt.py` |
| 6 | Build Executor node | `agent/nodes/executor.py` |
| 7 | Wire LangGraph workflow | `agent/graph.py` |
| 8 | Create FastAPI endpoints | `api/routes.py` |
| 9 | Update main.py entry point | `main.py` |
| 10 | Test with sample cases | Manual + unit tests |

---

## Key Dependencies (already in requirements.txt)
- `langchain` + `langchain-core` - LLM integration
- `langgraph` - Agent workflow/state graph (add to requirements.txt)
- `langchain-deepseek` - LLM model
- `fastapi` + `uvicorn` - API server
- `sqlite3` (built-in) - Database

---

## database.py Implementation Logic

```python
import sqlite3
import os

DB_PATH = "data.db"

def create_database():
    db_exists = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not db_exists:
        # Pehli baar - tables + seed data banao
        # CREATE TABLE users, orders, products
        # INSERT seed data
        # CREATE INDEXES
        conn.commit()
        print("Database created with seed data!")
    else:
        print("Connected to existing database.")

    return conn
```

**Flow:**
```
python main.py → database.py → data.db exists?
                                  ├── No  → Create tables + seed data + indexes → Return connection
                                  └── Yes → Return existing connection (skip seed)
```

---

## .gitignore Entry

```
# Database
data.db
__pycache__/
*.pyc
.venv/
```
