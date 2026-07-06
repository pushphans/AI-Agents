from starlette.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data
    assert "docs" in data


def test_chat_endpoint_exists():
    resp = client.post("/chat", json={"message": "hello", "session_id": "test1"})
    assert resp.status_code == 200


def test_chat_endpoint_response_structure():
    resp = client.post("/chat", json={"message": "show me blue shoes", "session_id": "test2"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "intent" in data
    assert isinstance(data["response"], str)
    assert isinstance(data["intent"], str)


def test_chat_product_search_intent():
    resp = client.post("/chat", json={"message": "i want to buy red shoes", "session_id": "test3"})
    data = resp.json()
    assert data["intent"] == "product_search"
    assert len(data["response"]) > 0


def test_chat_order_tracking_intent():
    resp = client.post("/chat", json={"message": "where is my order ORD123", "session_id": "test4"})
    data = resp.json()
    assert data["intent"] == "order_tracking"
    assert len(data["response"]) > 0


def test_chat_returns_intent():
    resp = client.post("/chat", json={"message": "i want to return an item", "session_id": "test5"})
    data = resp.json()
    assert data["intent"] == "returns"
    assert len(data["response"]) > 0


def test_chat_promotions_intent():
    resp = client.post("/chat", json={"message": "any discounts available", "session_id": "test6"})
    data = resp.json()
    assert data["intent"] == "promotions"
    assert len(data["response"]) > 0


def test_chat_payment_support_intent():
    resp = client.post("/chat", json={"message": "my payment failed", "session_id": "test7"})
    data = resp.json()
    assert data["intent"] == "payment_support"
    assert len(data["response"]) > 0


def test_chat_default_session_id():
    resp = client.post("/chat", json={"message": "show offers"})
    assert resp.status_code == 200
    data = resp.json()
    assert "intent" in data
