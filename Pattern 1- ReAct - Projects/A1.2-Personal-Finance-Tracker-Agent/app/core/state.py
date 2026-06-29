from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict, Optional
from langchain.messages import AnyMessage


class AgentState(TypedDict):
    messages : Annotated[list[AnyMessage], add_messages]

