from fastapi import APIRouter, HTTPException
from langchain.messages import HumanMessage

from app.agents.workflow import workflow
from app.core.state import AgentState
from app.models.models import RequestModel, ResponseModel

router = APIRouter(prefix="/agent")


@router.post("/ask-the-agent")
async def ask_the_agent(request: RequestModel):
    try:
        init_state: AgentState = {
            "messages": [HumanMessage(content=request.query)],
            "route": None,
        }

        final_state: AgentState = await workflow.ainvoke(init_state)

        return ResponseModel(
            answer=final_state["messages"][-1].content,
            router=final_state["route"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
