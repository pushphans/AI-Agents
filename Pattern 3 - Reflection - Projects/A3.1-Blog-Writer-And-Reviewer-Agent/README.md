# Blog Writer & Reviewer Agent

An AI-powered blog generation pipeline with built-in self-review and iterative improvement. Uses **LangGraph** for orchestration and **DeepSeek** as the LLM backend.

## How It Works

```
User: Topic → Generator (draft) → Critic (evaluate 6 criteria)
                                   ↓ fail + retries left
                                 Generator (improve) → Critic ...
                                   ↓ pass OR max retries exhausted
                                 Final blog output
```

- **Generator** drafts a blog on the given topic
- **Critic** evaluates against 6 criteria (length, topic coverage, grammar, factual accuracy, SEO keywords, readability)
- On failure, the generator rewrites incorporating feedback — up to 3 iterations
- Returns the final blog once quality passes, or after max retries

## Architecture

```
app/
├── agent/
│   └── workflow.py       # LangGraph state graph (generate → evaluate → loop)
├── api/
│   └── router.py         # FastAPI router (/api/generate-blog)
├── core/
│   └── config.py         # Pydantic settings (reads DEEPSEEK_API_KEY)
└── models/
    └── schemas.py        # Request/response + structured output models
main.py                    # FastAPI app entrypoint
tests/
└── test_workflow.py      # Unit tests (schema, workflow, API)
```

## Setup

### Prerequisites

- Python ≥ 3.12
- uv (recommended) or pip

### Install

```bash
uv sync
# or
pip install -r requirements.txt
```

### Environment

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Usage

### Start the API server

```bash
python main.py
```

Server starts at `http://localhost:8000`.

### Generate a blog

```bash
curl -X POST http://localhost:8000/api/generate-blog \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in healthcare", "max_iterations": 3}'
```

**Response:**

```json
{
  "success": true,
  "blog_content": "The blog content...",
  "iterations_taken": 2,
  "evaluation": "pass",
  "feedback": "Detailed evaluation feedback..."
}
```

Tests use mocked LLM calls — no API key required. Run:

```bash
pytest tests/ -v
```

## Technology Stack

| Component      | Library             |
|----------------|---------------------|
| LLM            | DeepSeek (langchain-deepseek) |
| Orchestration  | LangGraph           |
| API            | FastAPI + uvicorn   |
| Config         | pydantic-settings   |

Evaluation criteria:
- **Length Check** — ~500 words
- **Topic Coverage** — thoroughness
- **Grammar & Clarity** — correctness
- **Factual Accuracy** — correctness of claims
- **SEO Keywords** — natural keyword usage
- **Readability** — structure and flow
