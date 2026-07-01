from typing import Annotated, Literal, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Optional[Literal["HR", "FACILITY", "DATA", "CHAT"]]
