import pytest

from app.agent.subworkflows import (
    order_tracking_workflow,
    payment_support_workflow,
    product_search_workflow,
    promotions_workflow,
    returns_workflow,
    reviews_rag_workflow,
)


def get_subgraph(module):
    return module.subgraph


@pytest.mark.parametrize("name,module", [
    ("product_search", product_search_workflow),
    ("order_tracking", order_tracking_workflow),
    ("returns", returns_workflow),
    ("reviews_rag", reviews_rag_workflow),
    ("payment_support", payment_support_workflow),
    ("promotions", promotions_workflow),
])
def test_subgraph_compiles(name, module):
    g = get_subgraph(module)
    assert g is not None


@pytest.mark.parametrize("name,module", [
    ("product_search", product_search_workflow),
    ("order_tracking", order_tracking_workflow),
    ("returns", returns_workflow),
    ("reviews_rag", reviews_rag_workflow),
    ("payment_support", payment_support_workflow),
    ("promotions", promotions_workflow),
])
def test_subgraph_has_correct_nodes(name, module):
    g = get_subgraph(module)
    nodes = list(g.get_graph().nodes.keys())
    assert "extractor" in nodes
    assert "tools" in nodes
    assert "responder" in nodes
    assert "__start__" in nodes
    assert "__end__" in nodes


@pytest.mark.parametrize("name,module,num_nodes", [
    ("product_search", product_search_workflow, 5),
    ("order_tracking", order_tracking_workflow, 5),
    ("returns", returns_workflow, 5),
    ("reviews_rag", reviews_rag_workflow, 5),
    ("payment_support", payment_support_workflow, 5),
    ("promotions", promotions_workflow, 5),
])
def test_subgraph_node_count(name, module, num_nodes):
    g = get_subgraph(module)
    nodes = list(g.get_graph().nodes.keys())
    assert len(nodes) == num_nodes, f"{name}: expected {num_nodes} nodes, got {len(nodes)}: {nodes}"


def test_product_search_has_correct_tools():
    from app.agent.subworkflows.product_search_workflow import tools
    tool_names = {t.name for t in tools}
    assert "search_products" in tool_names
    assert "get_product_detail" in tool_names


def test_reviews_rag_has_correct_tools():
    from app.agent.subworkflows.reviews_rag_workflow import tools
    tool_names = {t.name for t in tools}
    assert "search_products" in tool_names
    assert "get_product_detail" in tool_names
    assert "get_product_reviews" in tool_names


@pytest.mark.parametrize("module,tool_name", [
    (order_tracking_workflow, "get_order_status"),
    (returns_workflow, "get_return_policy"),
    (payment_support_workflow, "get_order_status"),
    (promotions_workflow, "get_active_offers"),
])
def test_single_tool_subworkflows(module, tool_name):
    tool_names = {t.name for t in module.tools}
    assert tool_names == {tool_name}
