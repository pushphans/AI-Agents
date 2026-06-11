from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages
from langchain.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
