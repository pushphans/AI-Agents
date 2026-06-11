import logging

from fastapi import APIRouter, HTTPException
from httpx import HTTPError
from langchain.messages import HumanMessage

from app.agent.graph import workflow
from app.core.agent_state import AgentState
from app.schemas.agent import AgentInput, AgentOutput

logger = logging.getLogger("github-agent.router")

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=AgentOutput)
async def chat(request: AgentInput) -> AgentOutput:
    logger.info("=" * 50)
    logger.info("📩 Request: %s", request.message[:200])

    init_state: AgentState = {"messages": [HumanMessage(content=request.message)]}

    config = {"configurable": {"thread_id": request.session_id}}

    try:
        result = await workflow.ainvoke(init_state, config=config)
        content = result["messages"][-1].content
        logger.info("📤 Response: %s", content[:200])
        logger.info("=" * 50)
        return AgentOutput(response=content)
    except HTTPError as e:
        logger.error("❌ GitHub API error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e}")
    except Exception as e:
        logger.error("❌ Internal error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
