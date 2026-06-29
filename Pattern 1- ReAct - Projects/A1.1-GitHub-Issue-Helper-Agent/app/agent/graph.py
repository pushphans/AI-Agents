from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from app.core.agent_state import AgentState
from app.core.config import settings
from app.core.tools import TOOLS

llm = init_chat_model(
    model="gpt-4o", model_provider="openai", api_key=settings.OPENAI_API_KEY
)
model_with_tools = llm.bind_tools(TOOLS)


async def agent_node(state: AgentState) -> AgentState:

    messages = state["messages"]
    system_message = SystemMessage(
        "You are a GitHub issue helper agent. "
        "You ONLY handle queries related to GitHub issues — listing, creating, closing, "
        "commenting, and assigning issues. "
        "If a user asks about anything else (code explanation, documentation, features, etc.), "
        "politely say you can only help with GitHub issue management."
    )
    print("🤖 Agent node triggered")
    try:
        result = await model_with_tools.ainvoke([system_message] + messages)
        return {"messages": [result]}
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return {
            "messages": [
                SystemMessage(
                    content=f"I'm sorry, I encountered an error while processing your request: {e}"
                )
            ]
        }


tool_node = ToolNode(tools=TOOLS)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", "__end__": END},
)
graph.add_edge("tools", "agent")

memory = InMemorySaver()

workflow = graph.compile(checkpointer=memory)
