import asyncio
from typing import Literal, Optional, TypedDict, Annotated

from langchain.messages import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.agent.subworkflows.order_tracking_workflow import (
    subgraph as order_tracking_subgraph,
)
from app.agent.subworkflows.payment_support_workflow import (
    subgraph as payment_support_subgraph,
)
from app.agent.subworkflows.product_search_workflow import (
    subgraph as product_search_subgraph,
)
from app.agent.subworkflows.promotions_workflow import subgraph as promotions_subgraph
from app.agent.subworkflows.returns_workflow import subgraph as returns_subgraph
from app.agent.subworkflows.reviews_rag_workflow import subgraph as reviews_rag_subgraph
from app.core.config import settings

# LLM Initialization
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    max_retries=2,
    temperature=0.0,
    request_timeout=30,
)


# Agent state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: Optional[str]


# Structured Output
class IntentResponse(BaseModel):
    intent: Literal[
        "product_search",
        "order_tracking",
        "returns",
        "reviews_rag",
        "payment_support",
        "promotions",
        "multi_intent",
    ] = Field(
        description="""Intent classified from user's query.
              It can onlybe one of the following:
              1. product_search
              2. order_tracking
              3. returns
              4. reviews_rag
              5. payment_support
              6. promotions
              7. multi_intent

              - If the user wants to buy something, it's always 'product_search'
              - If the user asks about order status, it's 'order_tracking'
              - If the user asks about returns, it's 'returns'
              - If the user asks about reviews, it's 'reviews_rag'
              - If the user asks about payments, it's 'payment_support'
              - If the user asks about offers, it's 'promotions'
              - If the user asks about multiple things, it's 'multi_intent'
              """
    )


router_llm = llm.with_structured_output(schema=IntentResponse)


async def router_node(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    system_message = SystemMessage(
        content="You are an expert at classifying user intents into pre-defined categories based on the conversation history."
    )

    response: IntentResponse = await router_llm.ainvoke([system_message, last_message])

    return {"intent": response.intent}


def product_search_node(state: AgentState) -> AgentState:
    return product_search_subgraph.invoke(state)


def order_tracking_node(state: AgentState) -> AgentState:
    return order_tracking_subgraph.invoke(state)


def returns_node(state: AgentState) -> AgentState:
    return returns_subgraph.invoke(state)


def reviews_rag_node(state: AgentState) -> AgentState:
    return reviews_rag_subgraph.invoke(state)


def payment_support_node(state: AgentState) -> AgentState:
    return payment_support_subgraph.invoke(state)


def promotions_node(state: AgentState) -> AgentState:
    return promotions_subgraph.invoke(state)


def routing_condition(state: AgentState) -> str:
    return state["intent"]


g = StateGraph(AgentState)

g.add_node("router", router_node)
g.add_node("product_search", product_search_node)
g.add_node("order_tracking", order_tracking_node)
g.add_node("returns", returns_node)
g.add_node("reviews_rag", reviews_rag_node)
g.add_node("payment_support", payment_support_node)
g.add_node("promotions", promotions_node)

g.set_entry_point("router")

g.add_conditional_edges(
    "router",
    routing_condition,
    {
        "product_search": "product_search",
        "order_tracking": "order_tracking",
        "returns": "returns",
        "reviews_rag": "reviews_rag",
        "payment_support": "payment_support",
        "promotions": "promotions",
    },
)

g.add_edge("product_search", END)
g.add_edge("order_tracking", END)
g.add_edge("returns", END)
g.add_edge("reviews_rag", END)
g.add_edge("payment_support", END)
g.add_edge("promotions", END)


workflow = g.compile(checkpointer=MemorySaver())


async def run_agent():
    init_state: AgentState = {
        "messages": HumanMessage(
            content="i want to search for footwears that are blue in colour"
        ),
        "intent": None,
    }

    final_state: AgentState = await workflow.ainvoke(init_state)

    print(final_state["intent"])

    print("\n\n")
    print(final_state["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(run_agent())
