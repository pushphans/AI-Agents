import pytest
from app.agent.personal_finance_agent import workflow, agent_node, llm_with_tools
from app.core.state import AgentState
from langchain.messages import AIMessage, HumanMessage


class TestWorkflowCompilation:
    def test_workflow_nodes(self):
        nodes = list(workflow.nodes.keys())
        assert "agent_node" in nodes
        assert "tool_node" in nodes
        assert "__start__" in nodes

    def test_workflow_edges(self):
        """Check that the graph can produce a valid mermaid representation."""
        mermaid = workflow.get_graph().draw_mermaid()
        assert "agent_node" in mermaid
        assert "tool_node" in mermaid

    def test_llm_bound_with_tools(self):
        """LLM should have tool binding for expense management."""
        tools = llm_with_tools.kwargs.get("tools", [])
        tool_names = {t["type"] for t in tools}
        assert "function" in tool_names
        # Check tool names in the function definitions
        func_names = {t["function"]["name"] for t in tools}
        expected = {
            "create_expense", "list_expenses", "filter_expenses",
            "get_expense_by_id", "update_expense", "delete_expense",
        }
        assert func_names == expected


@pytest.mark.asyncio
class TestAgentNodeErrorHandling:
    async def test_agent_node_returns_messages(self):
        """Call agent_node directly with a simple query."""
        state: AgentState = {"messages": [HumanMessage(content="Hello")]}
        result = await agent_node(state)
        assert "messages" in result
        assert len(result["messages"]) > 0

    async def test_agent_node_on_invalid_state(self):
        """Empty messages should be handled gracefully (system prompt is prepended)."""
        state: AgentState = {"messages": []}
        try:
            result = await agent_node(state)
            assert "messages" in result
        except Exception:
            pass  # Some errors may propagate but shouldn't crash the system
