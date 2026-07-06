from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from app.agent.workflow import workflow


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str


async def chat_handler(request: ChatRequest) -> ChatResponse:
    config: RunnableConfig = {"configurable": {"thread_id": request.session_id}}

    output = await workflow.ainvoke(
        {"messages": [HumanMessage(content=request.message)], "intent": None},
        config,
    )

    return ChatResponse(
        response=output["messages"][-1].content,
        intent=output["intent"],
    )
