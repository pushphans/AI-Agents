# E-Commerce Shopping Assistant

AI-powered multi-intent e-commerce assistant built with **LangGraph** and **FastAPI**. Routes user queries to specialized agents for product search, order tracking, returns, reviews, payment support, and promotions.

## Architecture

```
User → FastAPI → Router (LLM intent classifier) → Conditional Edge →
├── Product Search Agent   → [search_products, get_product_detail]
├── Order Tracking Agent   → [get_order_status]
├── Returns Agent          → [get_return_policy]
├── Reviews/RAG Agent      → [search_products, get_product_detail, get_product_reviews]
├── Payment Support Agent  → [get_order_status]
└── Promotions Agent       → [get_active_offers]
```

Each agent is a linear 3-node subgraph: **Extractor** (LLM forces tool call) → **ToolNode** → **Responder** (formats answer).

## Stack

- **LangGraph** — State graph orchestration with session memory
- **FastAPI** — REST API
- **ChatDeepSeek** — LLM
- **Pydantic** — Structured outputs & request validation
- **pytest** — 66 tests

## Setup

```bash
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv sync
cp .env.example .env        # add your API keys
```

## Run

```bash
uvicorn main:app --reload
# → http://localhost:8000/docs
```

## API

`POST /chat`

```json
{"message": "show me blue running shoes", "session_id": "user123"}
```

```json
{"response": "Here are the blue running shoes I found...", "intent": "product_search"}
```

## Tests

```bash
pytest tests/ -v
```

## Data

Structured dummy data in `data/`:
- 25 products across 7 categories
- 6 orders with various statuses
- 6 active promotional offers
- 23 product reviews
- Return policy with category-specific rules
