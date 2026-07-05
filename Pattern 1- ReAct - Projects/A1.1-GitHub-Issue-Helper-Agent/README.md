# GitHub Issue Helper Agent

An AI-powered conversational agent that manages GitHub issues through natural language. Built with **LangGraph**, **FastAPI**, and **OpenAI GPT-4o** — it can list, create, close, comment on, and assign issues across any GitHub repository.

---

## Features

- **List issues** — View open/closed issues from any repository
- **Create issues** — Open new issues with title and description
- **Close issues** — Close existing issues by number
- **Add comments** — Comment on any issue
- **Assign issues** — Assign issues to GitHub collaborators

All interactions happen through a simple chat interface — no need to remember GitHub CLI commands or API endpoints.

---

## Architecture

```
User Request
    │
    ▼
┌──────────────────────┐
│   FastAPI Server     │  POST /api/agent/chat
│   (app/main.py)      │  GET  /health
│   (app/api/router.py)│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│   LangGraph ReAct Agent              │
│                                      │
│   ┌──────────┐                       │
│   │  Agent   │  GPT-4o + 5 tools     │
│   │  Node    │  ─→ reply or tool call│
│   └────┬─────┘                       │
│        │                             │
│   ┌────┴─────┐                       │
│   │  Tools   │  tools_condition      │
│   │  Node    │  routes tool calls    │
│   └────┬─────┘                       │
│        │  (loop back to Agent)       │
│        ▼                             │
│   ┌──────────┐                       │
│   │  Memory  │  InMemorySaver        │
│   │  Saver   │  (per session_id)     │
│   └──────────┘                       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   GitHub REST API    │  Authenticated via
│   (api.github.com)   │  GITHUB_TOKEN
└──────────────────────┘
```

### Agent Loop

1. **System prompt** restricts the agent to GitHub issue management only
2. **LLM (GPT-4o)** receives the conversation history and decides:
   - Respond directly → route to **END**
   - Call a tool → route to **Tool Node**
3. **Tool Node** executes the GitHub API call via `httpx`
4. Results feed back to the LLM for interpretation
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
| OpenAI GPT-4o | Language model |
| LangChain-OpenAI | OpenAI integration |
| GitHub REST API | Issue management operations |
| httpx | Async HTTP client |
| Pydantic / Pydantic-Settings | Validation & configuration |
| LangSmith | LLM tracing & observability |
| Tenacity | Retry utilities |
| pytest | Testing |
| uv | Package manager |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key
- GitHub personal access token with `repo` scope

### Installation

```bash
# Clone and enter the project
cd A1.1-GitHub-Issue-Helper-Agent

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
GITHUB_TOKEN=ghp_your-github-token

# Optional: LangSmith tracing
LANGSMITH_API_KEY=lsv2_your-langsmith-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=A1.1-GitHub-Issue-Helper-Agent
```

### Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

## API Reference

### `POST /api/agent/chat`

Send a message to the agent and receive a response.

**Request body:**

```json
{
  "message": "Show me open issues in langchain-ai/langchain",
  "session_id": "user-session-123"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Natural language request (required) |
| `session_id` | string | Session identifier for conversation memory |

**Response body:**

```json
{
  "response": "Here are the open issues in langchain-ai/langchain:\n\n1. ...",
  "session_id": "user-session-123"
}
```

### `GET /health`

Health check endpoint. Returns `{"status": "healthy"}`.

---

## Tools

Each tool maps to a GitHub REST API operation with input validation via Pydantic schemas.

| Tool | GitHub API | Description |
|------|------------|-------------|
| `list_issues` | `GET /repos/{owner}/{repo}/issues` | List issues with optional state filter (`open`, `closed`, `all`) |
| `create_issue` | `POST /repos/{owner}/{repo}/issues` | Create a new issue with title and optional body |
| `close_issue` | `PATCH /repos/{owner}/{repo}/issues/{number}` | Close an issue by number |
| `add_comment` | `POST /repos/{owner}/{repo}/issues/{number}/comments` | Add a comment to an issue |
| `assign_issue` | `POST /repos/{owner}/{repo}/issues/{number}/assignees` | Assign issue to GitHub usernames |

All repository inputs must follow the `owner/repo` format (validated by regex).

---

## Project Structure

```
A1.1-GitHub-Issue-Helper-Agent/
├── .env                         # Environment variables (excluded from VCS)
├── .gitignore
├── .python-version              # Python 3.12
├── pyproject.toml               # Project metadata & dependencies
├── requirements.txt             # Pip dependencies
├── uv.lock                      # Lock file
├── README.md
└── app/
    ├── __init__.py
    ├── main.py                  # FastAPI application entry point
    ├── core/
    │   ├── __init__.py
    │   ├── config.py            # Pydantic settings from .env
    │   ├── tools.py             # GitHub API tool implementations
    │   └── agent_state.py       # LangGraph state definition
    ├── schemas/
    │   ├── __init__.py
    │   ├── tools.py             # Pydantic input schemas for tools
    │   └── agent.py             # Pydantic schemas for API I/O
    ├── api/
    │   ├── __init__.py
    │   └── router.py            # FastAPI router (POST /api/agent/chat)
    └── agent/
        └── graph.py             # LangGraph state graph definition
```

---

## Error Handling

- **GitHub API errors** (timeout, connection, HTTP errors) — caught per-tool with descriptive messages
- **Invalid input** (malformed `owner/repo`, missing fields) — Pydantic validation returns 422
- **Off-topic queries** — system prompt instructs the agent to politely decline
- **Server errors** — FastAPI global exception handler logs and returns 500

---

## Conversation Memory

The agent uses LangGraph's `InMemorySaver` with `thread_id` = `session_id`, enabling contextual follow-ups within a session.

**Example conversation:**

```
User:   Show me open issues in my-org/my-repo
Agent:  Here are the open issues: #1 "Bug in login" ...

User:   Close issue #1
Agent:  Issue #1 "Bug in login" has been closed.

User:   What was my last action?
Agent:  You just closed issue #1 "Bug in login" in my-org/my-repo.
```
