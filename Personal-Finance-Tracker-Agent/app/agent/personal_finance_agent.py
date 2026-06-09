import asyncio
from datetime import datetime
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from app.core.state import AgentState
from app.core.config import settings
from app.core.tools import ALL_TOOLS
from langgraph.prebuilt import ToolNode, tools_condition

llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai",
    api_key=settings.OPENAI_API_KEY,
)


llm_with_tools = llm.bind_tools(tools=ALL_TOOLS)


async def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    current_date = datetime.now()

    system_message = SystemMessage(content=f"""
You are a personal expense management agent. You have to manage user's finance by saving expenses to the storage, fetching expenses from storage on basis of user's query. 
You have access to tools create_expense, list_expenses, filter_expenses, get_expense_by_id, update_expense, delete_expense. Make sure to always use tools for accurate responses.
If user asks for fetching the expenses for a time period, then user the current date : {current_date}, calculate exact required priod and use filter tool for accurate filtering of data.
""")

    try:
        response = await llm_with_tools.ainvoke([system_message] + messages)
    except Exception as e:
        response = AIMessage(
            content=f"I encountered an error ({type(e).__name__}) while processing your request. Please try again.",
        )

    return {
        "messages": [response],
    }


tool_node = ToolNode(tools=ALL_TOOLS)


graph = StateGraph(state_schema=AgentState)
graph.add_node("agent_node", agent_node)
graph.add_node("tool_node", tool_node)


graph.add_edge(START, "agent_node")
graph.add_conditional_edges(
    "agent_node", tools_condition, {"tools": "tool_node", "__end__": END}
)
graph.add_edge("tool_node", "agent_node")


workflow = graph.compile()


# async def run_agent(user_message: str):
#     init_state: AgentState = {"messages": [HumanMessage(content=user_message)]}

#     final_state: AgentState = await workflow.ainvoke(init_state)

#     return final_state["messages"][-1].content


# if __name__ == "__main__":
#     asyncio.run(run_agent(user_message="what is my total spend this week"))
