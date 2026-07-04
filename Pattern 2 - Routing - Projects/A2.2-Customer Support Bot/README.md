# Customer Support Bot

**Pattern:** Routing (Pattern 2)
**Stack:** LangGraph + DeepSeek + ChromaDB
**RAG:** General support node pe ChromaDB se context retrieve karke answer

---

## Idea

Ek **router** user ka message classify karta hai aur usse sahi **specialized handler** tak bhejta hai. General inquiries pe **RAG** (ChromaDB) se knowledge base retrieve karke answer laata hai. Complaint route dedicated complaint handler ko bhejta hai.

---

## Routes (5 handlers)

| Route | Kab trigger hoga | Handler kya karega |
|-------|------------------|--------------------|
| `BILLING_SUPPORT` | Payment / invoice / refund issue | Billing handler node se reply |
| `TECH_SUPPORT` | Technical problem / bug / error | Tech support handler node se reply |
| `GENERAL_SUPPORT` | General inquiry / "how do I..." | **RAG** — ChromaDB se relevant context la kar answer |
| `COMPLAINT_SUPPORT` | Shikayat / naaraazgi | Complaint handler node se empathetic reply |
| `FEEDBACK_SUPPORT` | Suggestion / feedback | Feedback handler node se acknowledgement |

---

## Architecture

### Folder structure

```
A2.2-Customer Support Bot/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── core/
│   │   ├── config.py              # Settings: API keys + ChromaDB config
│   │   └── state.py               # AgentState TypedDict
│   ├── agent/
│   │   └── agent_graph.py         # LangGraph: router + 5 handler nodes
│   ├── models/
│   │   └── models.py              # RequestModel / ResponseModel (pydantic)
│   ├── rag/
│   │   ├── embeddings.py          # HuggingFace embedder (shared)
│   │   ├── ingestion/
│   │   │   ├── ingestion.py       # PDF -> chunks -> embeddings (core logic)
│   │   │   └── run_ingestion.py   # One-time script: PDF -> ChromaDB
│   │   ├── retrieval/
│   │   │   └── retrieval.py       # query -> ChromaDB -> relevant chunks
│   │   └── vector_db/
│   │       └── vector_database.py # ChromaDB instance
│   └── sample_data/
│       └── test_data.pdf          # Sample PDF for RAG knowledge base
├── data/
│   └── chroma_db/                 # ChromaDB persistent storage (auto-created)
├── requirements.txt
├── pyproject.toml
├── .env                           # API keys (git-ignored)
└── README.md
```

### LangGraph flow

```
START ──────► router_node (classifies query into one of 5 routes)
              │
              ├── BILLING_SUPPORT ──► billing_node ──► END
              ├── TECH_SUPPORT ────► tech_node ──────► END
              ├── GENERAL_SUPPORT ─► general_node ────► END (RAG enabled)
              ├── COMPLAINT_SUPPORT ► complaint_node ──► END
              └── FEEDBACK_SUPPORT ► feedback_node ───► END
```

**RAG flow (GENERAL_SUPPORT route):**
```
User query
    │
    ▼
retrieve_data(query) ──► ChromaDB.asimilarity_search()
    │                        │
    │                        ▼
    │                    top-k similar chunks
    │                        │
    ▼                        ▼
System prompt + context ──► LLM ──► Answer
```

---

## State schema

`app/core/state.py`

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Optional[str]
```

---

## Components

### Router node
- LLM se structured output lekar user query ko 5 routes mein classify karta hai.
- Complaint, billing, tech, feedback, general — har category ka alag handler.

### Handler nodes (5)
- `billing_node` — billing/payment/invoice related queries
- `tech_node` — technical issues, bugs, setup
- `general_node` — general queries. **RAG enabled**: ChromaDB se relevant context retrieve karke LLM ko deta hai.
- `complaint_node` — complaints, escalations (empathetic response)
- `feedback_node` — suggestions, feature requests

### RAG module (`app/rag/`)
- **ingestion/ingestion.py** — PDF file read → text chunks → embeddings
- **ingestion/run_ingestion.py** — One-time script: `test_data.pdf` se chunks banake ChromaDB mein store karta hai
- **retrieval/retrieval.py** — User query se ChromaDB mein top-k similar chunks dhundhta hai
- **vector_db/vector_database.py** — ChromaDB instance (persistent, file-based)

### Vector DB: ChromaDB
- **Qdrant se migrate** kiya hai ChromaDB pe
- File-based persistent storage (`data/chroma_db/`)
- Collection auto-create hota hai, koi manual check nahi chahiye
- `HuggingFaceEmbeddings` (all-MiniLM-L6-v2) use ho raha hai

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure `.env`

`.env` file mein DeepSeek API key daalo:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 3. Ingest PDF into ChromaDB (one-time)

Sample PDF (`app/sample_data/test_data.pdf`) se data ChromaDB mein load karne ke liye:

```bash
python -m app.rag.ingestion.run_ingestion
```

Yeh script ek baar chalana hai. ChromaDB mein data permanently store ho jayega (`data/chroma_db/`).

Agar naya PDF daalna ho toh `run_ingestion.py` mein path change karo aur phir se chalao.

### 4. Run the agent

```bash
python -m app.agent.agent_graph
```

---

## How it works

1. User query aati hai → router classify karta hai
2. Route ke hisaab se appropriate node chalta hai
3. `GENERAL_SUPPORT` route pe:
   - `retrieve_data()` ChromaDB se relevant chunks laata hai
   - Context system prompt mein inject hota hai
   - LLM context ke saath answer generate karta hai
4. Agar relevant context na mile, LLM "I cannot answer this question" bolta hai

---

## Tech stack

| Component | Technology |
|-----------|-----------|
| LLM | DeepSeek (deepseek-chat) |
| Agent Framework | LangGraph |
| Vector DB | ChromaDB (persistent) |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| PDF Processing | pypdf |
| Text Splitting | RecursiveCharacterTextSplitter |
| API | FastAPI (planned) |
