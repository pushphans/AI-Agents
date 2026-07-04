import asyncio
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.state import AgentState
from app.rag.retrieval.retrieval import retrieve_data

# LLM
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.deepseek_api_key,
    temperature=0.0,
    max_retries=2,
)


# STRUCTURED OUTPUT SCHEMAS
class RouterOutputSchema(BaseModel):
    route: Literal[
        "BILLING_SUPPORT",
        "TECH_SUPPORT",
        "GENERAL_SUPPORT",
        "COMPLAINT_SUPPORT",
        "FEEDBACK_SUPPORT",
    ] = Field(description="Routes classified by the router from user's query")


router_llm = llm.with_structured_output(schema=RouterOutputSchema)


# NODES
# ===== ROUTER NODE =====
async def router_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="""You are a router that classifies user queries into one of the following categories: BILLING_SUPPORT, TECH_SUPPORT, GENERAL_SUPPORT, COMPLAINT_SUPPORT, FEEDBACK_SUPPORT.
            If user's query is about billing, classify it as BILLING_SUPPORT.
            If user's query is about tech, classify it as TECH_SUPPORT.
            If user's query is about complaint, classify it as COMPLAINT_SUPPORT.
            If user's query is about feedback, classify it as FEEDBACK_SUPPORT.
            If user's query is about general support, classify it as GENERAL_SUPPORT.
            If the user query does not fit into any of these categories, classify it as GENERAL_SUPPORT.
        """
    )

    # Pass full message history to LLM for routing decision
    response: RouterOutputSchema = await router_llm.ainvoke([system_message] + messages)
    return {"route": response.route}


# ===== ROUTING FUNCTION =====
async def routing_function(
    state: AgentState,
) -> Literal[
    "BILLING_SUPPORT",
    "TECH_SUPPORT",
    "GENERAL_SUPPORT",
    "COMPLAINT_SUPPORT",
    "FEEDBACK_SUPPORT",
]:

    route = state["route"]
    if route == "BILLING_SUPPORT":
        return "BILLING_SUPPORT"
    elif route == "TECH_SUPPORT":
        return "TECH_SUPPORT"
    elif route == "GENERAL_SUPPORT":
        return "GENERAL_SUPPORT"
    elif route == "COMPLAINT_SUPPORT":
        return "COMPLAINT_SUPPORT"
    elif route == "FEEDBACK_SUPPORT":
        return "FEEDBACK_SUPPORT"
    else:
        return "GENERAL_SUPPORT"


# ===== BILLING SUPPORT NODE =====
async def billing_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="""You are a billing support agent that helps users with their questions.
            Provide clear, helpful, and polite responses about billing, payments, invoices, refunds, subscriptions, and pricing."""
    )

    response = await llm.ainvoke([system_message] + messages)
    return {"messages": [response]}


# ===== TECHNICAL SUPPORT NODE =====
async def tech_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="""You are a technical support agent that helps users with their questions.
            Provide clear, helpful, and polite responses about technical issues, troubleshooting, software bugs, setup, and configuration."""
    )

    response = await llm.ainvoke([system_message] + messages)
    return {"messages": [response]}


# ===== GENERAL SUPPORT NODE =====
async def general_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    last_message = state["messages"][-1]

    context = await retrieve_data(query=last_message.content)
    print(str(context))
    print("\n")

    system_message = SystemMessage(
        content=f"""You are a general support agent that helps users with their general questions.
            Provide clear, helpful, and polite responses about company information, policies, account management, and general inquiries.
            You have to use this context to answer user's query if you dont have proper r relevant context to answer user's query
            just simply response with "i cannot answer this question".

            context : {context}
            """
    )

    response = await llm.ainvoke([system_message] + messages)
    return {"messages": [response]}


# ===== COMPLAINT HANDLING NODE =====
async def complaint_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="""You are a complaints handling agent that helps users with their complaints.
            Provide empathetic, clear, and helpful responses about complaints, issues, escalations, and resolutions."""
    )

    response = await llm.ainvoke([system_message] + messages)
    return {"messages": [response]}


# ===== FEEDBACK HANDLING NODE =====
async def feedback_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    system_message = SystemMessage(
        content="""You are a feedback handling agent that helps users with their feedback.
            Provide appreciative, clear, and helpful responses about feedback, suggestions, feature requests, and reviews."""
    )

    response = await llm.ainvoke([system_message] + messages)
    return {"messages": [response]}


# GRAPH
graph = StateGraph(state_schema=AgentState)
graph.add_node("router_node", router_node)
graph.add_node("billing_node", billing_node)
graph.add_node("tech_node", tech_node)
graph.add_node("complaint_node", complaint_node)
graph.add_node("feedback_node", feedback_node)
graph.add_node("general_node", general_node)

graph.add_edge(START, "router_node")
graph.add_conditional_edges(
    "router_node",
    routing_function,
    {
        "BILLING_SUPPORT": "billing_node",
        "TECH_SUPPORT": "tech_node",
        "COMPLAINT_SUPPORT": "complaint_node",
        "FEEDBACK_SUPPORT": "feedback_node",
        "GENERAL_SUPPORT": "general_node",
    },
)

graph.add_edge("billing_node", END)
graph.add_edge("tech_node", END)
graph.add_edge("complaint_node", END)
graph.add_edge("feedback_node", END)
graph.add_edge("general_node", END)


checkpointer = MemorySaver()
workflow = graph.compile(checkpointer=checkpointer)


async def run_workflow():
    init_state: AgentState = {
        "messages": [HumanMessage(content="any news related to ABHA?")]
    }

    config = {"configurable": {"thread_id": "pushp@123"}}

    final_state: AgentState = await workflow.ainvoke(init_state, config=config)

    print("\n")
    print("============RESPONSE==============")
    print(final_state["messages"][-1].content)
    print("\n")
    print("============ROUTE==============")
    print(final_state["route"])


asyncio.run(run_workflow())
