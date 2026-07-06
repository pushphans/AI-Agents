from typing import Annotated

from langchain_core.messages import BaseMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from app.core.config import settings
from app.core.tools import get_product_detail, get_product_reviews, search_products

llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    max_retries=2,
    temperature=0.0,
    request_timeout=30,
)

tools = [search_products, get_product_detail, get_product_reviews]

extractor = llm.bind_tools(tools, strict=True, tool_choice="any")
tool_node = ToolNode(tools)

responder = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    max_retries=2,
    temperature=0.0,
    request_timeout=30,
)


class SubworkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def extractor_node(state: SubworkflowState) -> dict:
    result = extractor.invoke(state["messages"])
    return {"messages": [result]}


def responder_node(state: SubworkflowState) -> dict:
    result = responder.invoke(state["messages"])
    return {"messages": [result]}


graph = StateGraph(SubworkflowState)
graph.add_node("extractor", extractor_node)
graph.add_node("tools", tool_node)
graph.add_node("responder", responder_node)

graph.add_edge(START, "extractor")
graph.add_edge("extractor", "tools")
graph.add_edge("tools", "responder")
graph.add_edge("responder", END)

subgraph = graph.compile()
