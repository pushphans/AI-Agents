import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import reset_database, get_schema_for_prompt
from app.agent.workflow import build_graph

router = APIRouter()


class ValidateRequest(BaseModel):
    question: str


class ValidateResponse(BaseModel):
    sql: str
    evaluation: Optional[str]
    iterations: int
    results: list[dict]
    error: Optional[str]


@router.post("/setup")
def setup():
    conn = reset_database()
    conn.close()

    return {
        "message": "Database created successfully with seed data",
        "db_path": settings.DB_PATH,
        "tables": ["users", "orders", "products"],
    }


@router.post("/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest):
    if not os.path.exists(settings.DB_PATH):
        raise HTTPException(
            status_code=400,
            detail="Database not found. Run /setup first to create the database.",
        )

    from langchain_deepseek import ChatDeepSeek

    llm = ChatDeepSeek(model="deepseek-chat", temperature=0, api_key=settings.DEEPSEEK_API_KEY)
    conn = reset_database()
    graph = build_graph(llm, conn)

    initial_state = {
        "user_question": request.question,
        "schema": get_schema_for_prompt(),
        "current_sql": "",
        "evaluation": None,
        "feedback": [],
        "current_iteration": 0,
        "max_iterations": settings.MAX_ITERATIONS,
        "query_results": None,
        "error": None,
    }

    result = graph.invoke(initial_state)
    conn.close()

    return ValidateResponse(
        sql=result["current_sql"],
        evaluation=result["evaluation"],
        iterations=result["current_iteration"],
        results=result.get("query_results") or [],
        error=result.get("error"),
    )
