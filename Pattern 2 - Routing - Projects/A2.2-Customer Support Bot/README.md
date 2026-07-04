# Project 2.2 — Customer Support Bot

**Pattern:** Routing (Pattern 2)
**Stack:** LangGraph + FastAPI + DeepSeek (A2.1 wali conventions same)
**Naya kya hai:** RAG as one route + confidence-based human escalation + priority routing

---

## 1. Idea (ek line mein)

Ek **router** customer ka message classify karta hai aur usse sahi **specialized handler** tak bhejta hai. General inquiries pe **RAG** knowledge base se answer laata hai; agar RAG confident na ho ya complaint ho to **human escalation** hota hai.

---

## 2. Routes (5 handlers)

| Route | Kab trigger hoga | Handler kya karega | Priority |
|-------|------------------|--------------------|----------|
| `BILLING` | Payment / invoice / refund issue | Billing handler node se reply | NORMAL |
| `TECH` | Technical problem / bug / error | Tech support handler node se reply | NORMAL |
| `FAQ` | General inquiry / "how do I..." | **RAG** — knowledge base se retrieve karke answer | LOW |
| `COMPLAINT` | Shikayat / naaraazgi | Priority handler + **human escalation** | HIGH |
| `FEEDBACK` | Suggestion / feedback | Storage handler — save kar do, koi LLM answer nahi | LOW |

---

## 3. Architecture

### Folder structure

```
A2.2-Customer Support Bot/
├── app/
│   ├── main.py                  # FastAPI app + router include
│   ├── api/
│   │   └── agent_router.py      # POST /agent/ask-the-agent
│   ├── agents/
│   │   └── workflow.py          # LangGraph: router node + 5 handler nodes
│   ├── core/
│   │   ├── config.py            # settings: API key + embedding/vector config
│   │   └── state.py             # AgentState TypedDict
│   ├── rag/
│   │   ├── ingest.py            # docs -> chunks -> embeddings -> vector store (one-time)
│   │   └── retriever.py         # query -> relevant chunks + similarity score
│   └── models/
│       └── models.py            # RequestModel / ResponseModel (pydantic)
├── data/
│   └── knowledge_base/          # FAQ docs (.md / .txt) — RAG source
├── requirements.txt
└── README.md
```

### LangGraph flow

```
                 ┌─────────────┐
   START ───────►│   ROUTER    │  structured output: route + priority
                 └──────┬──────┘
        ┌───────┬───────┼───────────┬────────────┐
        ▼       ▼       ▼           ▼            ▼
     BILLING  TECH   FAQ_RAG    COMPLAINT     FEEDBACK
      node    node   node │      node │        node
        │       │         │          │           │
        │       │   confidence?   escalate=True   │
        │       │    ┌────┴────┐      │           │
        │       │  high      low      │           │
        │       │   │          │      │           │
        │       │ answer   ESCALATE ◄─┘           │
        └───────┴────┬─────────┴──────────────────┘
                     ▼
                    END
```

---

## 4. State schema

`app/core/state.py` — A2.1 ke `AgentState` ko extend karke:

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Optional[Literal["BILLING", "TECH", "FAQ", "COMPLAINT", "FEEDBACK"]]
    priority: Optional[Literal["LOW", "NORMAL", "HIGH"]]
    rag_confidence: Optional[float]   # RAG similarity score (0-1)
    escalated: bool                    # human handoff flag
```

---

## 5. Components — kya-kya banana hai

### 5.1 Router node
- Structured output (pydantic schema) se `route` + `priority` dono nikaalo.
- Complaint aaye to `priority = HIGH`.
- A2.1 ke `router_node` jaisa hi, bas priority field extra.

### 5.2 Handler nodes (5)
- `billing_node`, `tech_node` — simple LLM + system prompt (A2.1 pattern).
- `faq_node` — **RAG**: retriever call karo, docs + score lao, LLM ko context ke saath answer generate karne do, `rag_confidence` state mein set karo.
- `complaint_node` — reply draft karo but `escalated = True` set karo.
- `feedback_node` — answer generate mat karo, message ko store (file/DB) karke acknowledgement do.

### 5.3 RAG module (`app/rag/`)
- **ingest.py** — `data/knowledge_base/` ke docs load -> chunk -> embed -> vector store (Chroma/FAISS). Ek baar chalta hai.
- **retriever.py** — query embed -> top-k similar chunks + similarity score return.

### 5.4 Confidence gate (escalation)
- FAQ node ke baad conditional edge:
  - `rag_confidence >= THRESHOLD` -> answer -> END
  - `rag_confidence < THRESHOLD` -> `ESCALATE` node -> END
- Complaint route hamesha escalate.

### 5.5 API layer
- `POST /agent/ask-the-agent` (A2.1 jaisa).
- `ResponseModel` mein extra fields: `route`, `priority`, `escalated`, `confidence`.

---

## 6. Naye concepts (yeh project seekhne ke liye hai)

1. **Smart routing with priorities** — router sirf route nahi, priority bhi decide karta hai.
2. **RAG as one route** — poora bot RAG nahi; sirf FAQ path pe RAG.
3. **Confidence-based decisions** — retrieval score dekhkar answer vs escalate.
4. **Escalation patterns** — human handoff flag + priority.

> A2.1 se difference: routing skeleton same hai. **Naya sirf RAG + confidence gate + escalation + priority hai.**

---

## 7. Build order (suggested)

1. `state.py` + `models.py` — schemas pehle.
2. Router node + 5 empty handler nodes + graph wiring (A2.1 se port).
3. FastAPI endpoint chalu karke basic routing test.
4. `data/knowledge_base/` mein 5-10 FAQ docs daalo.
5. `rag/ingest.py` + `rag/retriever.py` bana ke vector store ready.
6. `faq_node` mein RAG plug karo.
7. Confidence gate + `escalate_node` add karo.
8. Complaint priority + feedback storage finish.

---

## 8. Config / env

`.env`:
```
DEEPSEEK_API_KEY=your_key_here
```
`config.py` mein add: embedding model naam, vector store path, `RAG_CONFIDENCE_THRESHOLD` (e.g. 0.7), `RAG_TOP_K` (e.g. 3).

---

## 9. Example requests (test ke liye)

| Query | Expected route | Escalated? |
|-------|----------------|-----------|
| "My invoice shows double charge" | BILLING | No |
| "App crashes on login" | TECH | No |
| "What are your working hours?" | FAQ (RAG) | No (agar doc mila) |
| "Your service is terrible, I want a refund now" | COMPLAINT | Yes (HIGH) |
| "You should add dark mode" | FEEDBACK | No |
| "Random unknown question not in docs" | FAQ (RAG) | Yes (low confidence) |
