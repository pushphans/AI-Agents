import asyncio
import logging
from fastapi import APIRouter, HTTPException
from langchain.messages import HumanMessage
from app.core.state import AgentState
from app.agent.personal_finance_agent import workflow
from app.schema.agent_schema import AgentRequest, AgentResponse
from app.core.observability import ObservabilityCallback
from tenacity import retry, stop_after_attempt, retry_if_exception_type, RetryError

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 30.0

router = APIRouter(prefix="/api/v1")


@router.post("/chat", response_model=AgentResponse)
@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError, OSError)),
)
async def chat(request: AgentRequest):

    obs = ObservabilityCallback()

    try:
        init_state: AgentState = {"messages": [HumanMessage(content=request.message)]}
        final_state: AgentState = await asyncio.wait_for(
            workflow.ainvoke(init_state, callbacks=[obs]),
            timeout=AGENT_TIMEOUT,
        )
        if not final_state.get("messages"):
            raise RuntimeError("Agent returned no messages.")
        return AgentResponse(response=final_state["messages"][-1].content)
    except RetryError as e:
        last_exc = e.last_attempt.exception()
        if isinstance(last_exc, asyncio.TimeoutError):
            logger.warning("Agent timed out after %d retries | trace=%s", 3, obs.summary())
            raise HTTPException(
                status_code=504,
                detail=f"Agent did not respond within {AGENT_TIMEOUT}s after 3 attempts.",
            )
        logger.error("Agent failed after retries: %s | trace=%s", last_exc, obs.summary())
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error("Unexpected error: %s | trace=%s", e, obs.summary(), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        )
