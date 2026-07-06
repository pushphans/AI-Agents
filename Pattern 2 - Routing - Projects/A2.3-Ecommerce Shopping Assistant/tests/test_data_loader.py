import json
from pathlib import Path

import pytest

from app.core.data_loader import load_offers, load_orders, load_products, load_return_policy, load_reviews


@pytest.fixture
def data_dir():
    return Path(__file__).resolve().parent.parent / "data"


def test_data_files_exist(data_dir):
    assert (data_dir / "products.json").exists()
    assert (data_dir / "orders.json").exists()
    assert (data_dir / "offers.json").exists()
    assert (data_dir / "reviews.json").exists()
    assert (data_dir / "return_policy.json").exists()


def test_products_loaded():
    products = load_products()
    assert len(products) == 25
    assert all(p["id"] for p in products)
    assert all(p["name"] for p in products)


def test_products_have_required_fields():
    products = load_products()
    for p in products:
        assert "id" in p
        assert "name" in p
        assert "category" in p
        assert "price" in p
        assert "color" in p
        assert "rating" in p
        assert "stock" in p


def test_products_unique_ids():
    products = load_products()
    ids = [p["id"] for p in products]
    assert len(ids) == len(set(ids)), "Duplicate product IDs found"


def test_orders_loaded():
    orders = load_orders()
    assert len(orders) == 6
    assert all(o["id"] for o in orders)


def test_orders_have_required_fields():
    orders = load_orders()
    for o in orders:
        assert "id" in o
        assert "customer" in o
        assert "items" in o
        assert "status" in o
        assert "payment_status" in o
        assert "total" in o


def test_orders_valid_statuses():
    orders = load_orders()
    valid = {"shipped", "delivered", "processing", "cancelled"}
    for o in orders:
        assert o["status"] in valid, f"Invalid status: {o['status']}"


def test_offers_loaded():
    offers = load_offers()
    assert len(offers) == 6
    assert all(o["code"] for o in offers)


def test_offers_have_required_fields():
    offers = load_offers()
    for o in offers:
        assert "code" in o
        assert "description" in o
        assert "active" in o
        assert "discount_percent" in o
        assert "min_cart_value" in o
        assert "valid_until" in o


def test_reviews_loaded():
    reviews = load_reviews()
    assert len(reviews) == 23
    assert all(r["product_id"] for r in reviews)
    assert all(r["user"] for r in reviews)


def test_reviews_valid_product_ids():
    reviews = load_reviews()
    products = load_products()
    product_ids = {p["id"] for p in products}
    for r in reviews:
        assert r["product_id"] in product_ids, f"Review references unknown product: {r['product_id']}"


def test_return_policy_loaded():
    policy = load_return_policy()
    assert "general" in policy
    assert "categories" in policy


def test_return_policy_general():
    policy = load_return_policy()
    gen = policy["general"]
    assert "return_window_days" in gen
    assert isinstance(gen["return_window_days"], int)
    assert gen["return_window_days"] > 0
    assert "condition" in gen
    assert "process" in gen
    assert "refund_timeline" in gen


def test_return_policy_categories():
    policy = load_return_policy()
    cats = policy["categories"]
    assert "footwear" in cats
    assert "clothing" in cats
    assert "electronics" in cats
    assert "groceries" in cats
    assert "accessories" in cats
    assert "sports" in cats
    assert "health" in cats


def test_products_all_categories():
    products = load_products()
    categories = set(p["category"] for p in products)
    expected = {"footwear", "electronics", "clothing", "accessories", "sports", "health", "groceries"}
    assert categories == expected, f"Missing categories: {expected - categories}"
