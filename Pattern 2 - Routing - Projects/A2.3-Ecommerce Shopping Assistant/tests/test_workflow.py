import pytest

from app.agent.workflow import workflow, routing_condition, AgentState, StateGraph


def test_workflow_compiles():
    assert workflow is not None


def test_workflow_has_all_nodes():
    g = workflow
    nodes = list(g.get_graph().nodes.keys())
    expected = {"__start__", "__end__", "router", "product_search", "order_tracking",
                "returns", "reviews_rag", "payment_support", "promotions"}
    for n in expected:
        assert n in nodes, f"Missing node: {n}"


def test_workflow_node_count():
    g = workflow
    nodes = list(g.get_graph().nodes.keys())
    assert len(nodes) == 9


def test_routing_condition():
    from app.agent.workflow import AgentState
    state = AgentState(messages=[], intent="product_search")
    assert routing_condition(state) == "product_search"

    state = AgentState(messages=[], intent="order_tracking")
    assert routing_condition(state) == "order_tracking"

    state = AgentState(messages=[], intent="returns")
    assert routing_condition(state) == "returns"

    state = AgentState(messages=[], intent="multi_intent")
    assert routing_condition(state) == "multi_intent"
