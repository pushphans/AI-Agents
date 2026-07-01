# 🏢 Multi-Purpose Office Assistant

> An intelligent office assistant that **routes** incoming requests to the right specialized agent — built with **LangGraph** and **FastAPI**.

This project demonstrates the **Routing Pattern** (Agentic Design Pattern #2): a single entry point receives a user query, a lightweight *router* classifies its intent, and the request is dispatched to the appropriate specialized handler.

---

## 📌 What It Does

A user sends a single query. A **router node** reads it, classifies the intent, and forwards it to one of four specialized agents:

| User says | Routed to | Handler |
|-----------|-----------|---------|
| *"I want to apply for leave"* | `HR` | HR Assistant |
| *"Book a projector for the meeting room"* | `FACILITY` | Facility Assistant |
| *"Give me last month's report"* | `DATA` | Data Assistant |
| *"Hey, how are you?"* | `CHAT` | Chat Assistant |

If the router is ever unsure, it safely falls back to the `CHAT` agent.

---

## 🧠 How It Works

The whole app is a single **LangGraph state machine**. The router is a *decision-making node* that uses an LLM with **structured output** — so it can only ever return one of the four valid routes (no free-form text, no parsing bugs).

```
                    ┌─────────────┐
      user query →  │   ROUTER    │  (classifies intent)
                    └──────┬──────┘
                           │  conditional edge
        ┌──────────┬───────┼────────┬──────────┐
        ▼          ▼       ▼        ▼          ▼
     ┌──────┐  ┌──────┐ ┌──────┐ ┌──────┐   (fallback)
     │  HR  │  │ DATA │ │FACIL.│ │ CHAT │
     └──┬───┘  └──┬───┘ └──┬───┘ └──┬───┘
        └─────────┴────────┴────────┘
                     ▼
                    END → response
```

**Flow:** `START → ROUTER → (HR | DATA | FACILITY | CHAT) → END`

---

## 🗂️ Project Structure

```
app/
├── main.py                 # FastAPI app entry point
├── api/
│   └── agent_router.py     # POST /agent/ask-the-agent endpoint
├── agents/
│   └── workflow.py         # LangGraph graph: router + specialized nodes
├── core/
│   ├── config.py           # Settings loaded from .env (pydantic-settings)
│   └── state.py            # AgentState (shared graph state)
└── models/
    └── models.py           # Request / Response schemas
```

---

## 🛠️ Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — graph-based agent orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)** — LLM abstractions
- **[DeepSeek](https://www.deepseek.com/)** (`deepseek-chat`) — the LLM
- **[FastAPI](https://fastapi.tiangolo.com/)** + **Uvicorn** — async API layer
- **Pydantic / pydantic-settings** — validation & config
- **Python 3.12+**

---

## 🚀 Getting Started

### 1. Clone & enter the project
```bash
cd "A2.1-Multi-Purpose Office Assistant"
```

### 2. Set up the environment

Using **uv** (recommended):
```bash
uv sync
```

Or with **pip**:
```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Create a `.env` file in the project root:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

The API will be live at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

---

## 📡 API Usage

**Endpoint:** `POST /agent/ask-the-agent`

**Request:**
```json
{
  "query": "I want to apply for 2 days of leave next week"
}
```

**Response:**
```json
{
  "answer": "Sure! I can help you apply for leave...",
  "router": "HR"
}
```

The `router` field tells you which specialized agent handled the request — useful for debugging and observability.

### Quick test with curl
```bash
curl -X POST http://127.0.0.1:8000/agent/ask-the-agent \
  -H "Content-Type: application/json" \
  -d '{"query": "Book a projector for tomorrow"}'
```

---

## 💡 Key Concepts Demonstrated

- **Intent classification & routing** — an LLM-powered decision node
- **Structured output** — `Literal` schema guarantees valid routes
- **Conditional edges** in LangGraph for dynamic branching
- **Safe fallback handling** — unknown intents default to `CHAT`
- **Clean architecture** — separated API, agents, core, and models layers

---

## 🗺️ Roadmap

Ideas for extending this project:

- [ ] **Human-in-the-loop (HITL)** — add an approval step for sensitive actions (e.g. bulk data deletion) using LangGraph's `interrupt()` + a checkpointer.
- [ ] **Real tool integrations** — connect the HR, Facility, and Data agents to actual systems/databases.

---

## 📄 License

This project is part of a personal learning series on **Agentic Design Patterns**.
Feel free to explore and learn from it.
