from typing import Annotated, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Optional[str]
