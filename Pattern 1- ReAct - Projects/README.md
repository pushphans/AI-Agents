# Pattern 1: ReAct Agent Projects

This repository contains two AI-powered agent applications built using the **ReAct (Reasoning + Acting)** pattern with **LangGraph** and **FastAPI**. Both agents leverage LLMs to understand natural language, reason about tasks, and execute tool calls autonomously.

---

## Projects Overview

| Project | Description | LLM | Tools |
|---------|-------------|-----|-------|
| [A1.1-GitHub-Issue-Helper-Agent](./A1.1-GitHub-Issue-Helper-Agent) | Manages GitHub issues via conversational chat | GPT-4o | List, create, close, comment, assign issues |
| [A1.2-Personal-Finance-Tracker-Agent](./A1.2-Personal-Finance-Tracker-Agent) | Tracks personal expenses through natural language | GPT-4o-mini | Create, list, filter, update, delete expenses |

---

## Architecture (Common Pattern)

Both projects follow the same layered architecture:

```
User Request
    │
    ▼
┌──────────────────────┐
│   FastAPI Server     │  REST API entry point
│   (main.py, router) │  - Request validation
│                      │  - Retry / error handling
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LangGraph Agent     │  ReAct loop
│                      │  ┌──────────┐
│                      │  │  Agent   │  LLM reasons & decides
│                      │  │  Node    │  ───→ Reply directly OR
│                      │  └────┬─────┘       call tools
│                      │       │
│                      │  ┌────┴─────┐
│                      │  │  Tools   │  Conditional: tools_condition
│                      │  │  Node    │  routes tool calls → execution
│                      │  └────┬─────┘
│                      │       │  (loops back to Agent Node)
│                      └───────┴───────────┘
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   External / Local   │  GitHub API (Project 1)
│   Services           │  CSV File  (Project 2)
└──────────────────────┘
```

### ReAct Loop Flow

1. **System Prompt** instructs the LLM on its role and available tools
2. **Agent Node** sends conversation + system prompt to the LLM
3. **LLM decides**: either respond directly or emit tool calls
4. **Conditional Edge** (`tools_condition`):
   - No tool calls → route to **END** (return final answer)
   - Tool calls → route to **Tool Node**
5. **Tool Node** executes each tool and returns results
6. Results loop back to **Agent Node** for LLM to synthesize a response
7. Cycle repeats until the LLM produces a final answer

---

## Shared Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Runtime |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **LangChain** | LLM abstraction & tool framework |
| **LangGraph** | State graph / agent orchestration |
| **OpenAI GPT models** | LLM backend |
| **Pydantic / Pydantic-Settings** | Schema validation & configuration |
| **LangSmith** | LLM observability & tracing |
| **Tenacity** | Retry logic |
| **pytest** | Testing |
| **uv** | Package manager |

---

## Project 1: GitHub Issue Helper Agent

**Location:** [`A1.1-GitHub-Issue-Helper-Agent/`](./A1.1-GitHub-Issue-Helper-Agent)

An AI assistant that manages GitHub repository issues through conversation.

### Capabilities

- **List issues** — View open/closed issues from any repository
- **Create issues** — Open new issues with title and body
- **Close issues** — Close existing issues by number
- **Add comments** — Comment on issues
- **Assign issues** — Assign issues to GitHub users

### API Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/chat` | Send a message to the agent |
| `GET` | `/health` | Health check |

### Request / Response

```json
// POST /api/agent/chat
{
  "message": "Show me open issues in langchain-ai/langchain",
  "session_id": "user-session-123"
}

// Response
{
  "response": "Here are the open issues in langchain-ai/langchain:\n\n...",
  "session_id": "user-session-123"
}
```

### Setup

```bash
cd A1.1-GitHub-Issue-Helper-Agent
cp .env.example .env     # Configure your API keys
uv venv
uv sync
uvicorn app.main:app --reload
```

**Required environment variables:**
- `OPENAI_API_KEY` — OpenAI API key
- `GITHUB_TOKEN` — GitHub personal access token (with `repo` scope)
- `LANGSMITH_API_KEY` — (Optional) LangSmith API key for tracing

### Tool Definitions

| Tool | GitHub API | Description |
|------|------------|-------------|
| `list_issues` | `GET /repos/{owner}/{repo}/issues` | List issues with optional state filter |
| `create_issue` | `POST /repos/{owner}/{repo}/issues` | Create a new issue |
| `close_issue` | `PATCH /repos/{owner}/{repo}/issues/{number}` | Close an existing issue |
| `add_comment` | `POST /repos/{owner}/{repo}/issues/{number}/comments` | Comment on an issue |
| `assign_issue` | `POST /repos/{owner}/{repo}/issues/{number}/assignees` | Assign issue to a user |

---

## Project 2: Personal Finance Tracker Agent

**Location:** [`A1.2-Personal-Finance-Tracker-Agent/`](./A1.2-Personal-Finance-Tracker-Agent)

An AI assistant that helps users manage personal expenses through natural language, with CSV-backed storage.

### Capabilities

- **Add expenses** — Record new expenses with type, amount, item, and date
- **List all expenses** — View all recorded expenses
- **Look up by ID** — Get details of a specific expense
- **Update expenses** — Modify any field of an existing expense
- **Filter expenses** — Filter by date range, type, amount range, or item name
- **Delete expenses** — Remove an expense record

### API Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat` | Send a message to the agent |

### Request / Response

```json
// POST /api/v1/chat
{
  "message": "How much did I spend on food this month?"
}

// Response
{
  "response": "You spent $500.00 on Food in June 2026."
}
```

### Setup

```bash
cd A1.2-Personal-Finance-Tracker-Agent
cp .env.example .env     # Configure your API keys
uv venv
uv sync
uvicorn app.main:app --reload
```

**Required environment variables:**
- `OPENAI_API_KEY` — OpenAI API key
- `LANGSMITH_API_KEY` — (Optional) LangSmith API key for tracing

### Tool Definitions

| Tool | Description |
|------|-------------|
| `create_expense` | Add a new expense (type, amount, item, optional date) |
| `list_expenses` | View all expenses as a markdown table |
| `get_expense_by_id` | Get a single expense by its ID |
| `update_expense` | Partially update an expense's fields |
| `filter_expenses` | Filter expenses by date, type, amount, item text |
| `delete_expense` | Remove an expense by ID |

### Data Storage

Expenses are stored in `data/expenses.csv` with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Auto-incrementing unique identifier |
| `date` | Date (YYYY-MM-DD) | Date of expense (defaults to today) |
| `expense_type` | String | Category (e.g., Food, Fuel, Clothing) |
| `amount` | Decimal | Expense amount (must be positive) |
| `item` | String | Description of the expense |

**Design features:**
- Thread-safe operations via `threading.Lock`
- Atomic file writes via temp file + `os.replace()`
- Auto-creation of `data/` directory if missing

### Running Tests

```bash
cd A1.2-Personal-Finance-Tracker-Agent
uv run pytest -v
```

Test coverage includes:
- Schema validation (boundary cases, invalid input)
- Tool CRUD operations (success & failure paths)
- Agent workflow compilation
- API endpoint behavior
- Edge cases (concurrency, corrupted CSV, filesystem errors)

---

## Running the Servers

Both projects are standalone FastAPI applications. Run each from its own terminal:

```bash
# Terminal 1 — GitHub Issue Helper
cd A1.1-GitHub-Issue-Helper-Agent
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Finance Tracker
cd A1.2-Personal-Finance-Tracker-Agent
uvicorn app.main:app --reload --port 8001
```

---

## Common Design Principles

1. **ReAct Pattern** — Agents reason step-by-step, deciding whether to respond directly or invoke tools
2. **LangGraph StateGraph** — Cyclic graph with conditional routing for tool execution
3. **Conversation Memory** — Session-based message history via `InMemorySaver` checkpointing
4. **Tool-as-a-Service** — Each operation is a LangChain tool with Pydantic-validated inputs
5. **Observability** — LangSmith tracing integrated for monitoring LLM calls and tool usage
6. **Graceful Error Handling** — Timeouts, retries, and informative error responses
7. **Scope Enforcement** — System prompts constrain the agent to its intended domain
