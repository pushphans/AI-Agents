from typing import Literal

from langchain.messages import SystemMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.state import AgentState

# LLM
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0,
    max_retries=2,
)


# STRUCTURE OUTPUT SCHEMA
class RouterOutputSchema(BaseModel):
    router: Literal["HR", "DATA", "FACILITY", "CHAT"] = Field(
        description="route for the router to choose the next agent to handle the request"
    )


# ROUTER LLM WITH STRUCTURED OUTPUT
router_llm = llm.with_structured_output(schema=RouterOutputSchema)


# NODES
async def router_node(state: AgentState) -> AgentState:

    user_message = state["messages"][-1]

    system_message = SystemMessage(
        content="""You are a router that determines which agent should handle a given request.
        - If the user asks for leave return 'HR'.
        - If he asks for booking a projector return 'FACILITY'.
        - If it asks for reports for a time period return 'DATA'.
        - If the user is just saying general hi hello or want to talk return 'CHAT'.
        """
    )

    result: RouterOutputSchema = await router_llm.ainvoke(
        [system_message, user_message]
    )

    return {"route": result.router}


async def routing_function(
    state: AgentState,
) -> Literal["HR", "DATA", "FACILITY", "CHAT"]:
    route = state["route"]

    if route == "HR":
        return "HR"
    elif route == "DATA":
        return "DATA"
    elif route == "FACILITY":
        return "FACILITY"
    elif route == "CHAT":
        return "CHAT"
    else:
        return "CHAT"


async def hr_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="You are an HR assistant, you will be listening to user's leave requests and response accordingly"
    )

    response = await llm.ainvoke([system_message] + messages)

    return {"messages": [response]}


async def data_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="You are a data assistant, you will be listening to user's data requests and response accordingly"
    )

    response = await llm.ainvoke([system_message] + messages)

    return {"messages": [response]}


async def facility_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="You are a facility assistant, you will be listening to user's facility requests and response accordingly"
    )

    response = await llm.ainvoke([system_message] + messages)

    return {"messages": [response]}


async def chat_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="You are a chat assistant, you will be listening to user's general questions and response accordingly"
    )

    response = await llm.ainvoke([system_message] + messages)

    return {"messages": [response]}


# GRAPH
graph = StateGraph(state_schema=AgentState)

graph.add_node("ROUTER", router_node)
graph.add_node("HR_NODE", hr_node)
graph.add_node("DATA_NODE", data_node)
graph.add_node("FACILITY_NODE", facility_node)
graph.add_node("CHAT_NODE", chat_node)

graph.add_edge(START, "ROUTER")
graph.add_conditional_edges(
    "ROUTER",
    routing_function,
    {
        "HR": "HR_NODE",
        "DATA": "DATA_NODE",
        "FACILITY": "FACILITY_NODE",
        "CHAT": "CHAT_NODE",
    },
)

graph.add_edge("HR_NODE", END)
graph.add_edge("DATA_NODE", END)
graph.add_edge("FACILITY_NODE", END)
graph.add_edge("CHAT_NODE", END)


checkpointer = MemorySaver()
workflow = graph.compile(checkpointer=checkpointer)
