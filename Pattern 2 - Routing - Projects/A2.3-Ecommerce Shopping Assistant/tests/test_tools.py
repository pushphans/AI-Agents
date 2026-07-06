import pytest

from app.core.tools import (
    get_active_offers,
    get_order_status,
    get_product_detail,
    get_product_reviews,
    get_return_policy,
    search_products,
)



def test_search_products_by_color():
    result = search_products.invoke({"color": "red"})
    assert "Classic Fit Red Running Shoes" in result
    assert "Striped Cotton T-Shirt" in result


def test_search_products_by_category():
    result = search_products.invoke({"category": "footwear"})
    assert "Red Running Shoes" in result
    assert "Blue Running Shoes" in result
    assert "Black Formal Leather" in result


def test_search_products_by_color_and_category():
    result = search_products.invoke({"color": "blue", "category": "footwear"})
    assert "Blue Running Shoes Pro" in result
    assert "Red" not in result


def test_search_products_by_brand():
    result = search_products.invoke({"brand": "SoundMax"})
    assert "Wireless Bluetooth Headphones" in result
    assert "Bluetooth Speaker Mini" in result


def test_search_products_no_results():
    result = search_products.invoke({"color": "purple", "category": "electronics"})
    assert "nahi mila" in result.lower() or "no products" in result.lower()


def test_search_products_price_range():
    result = search_products.invoke({"min_price": 3000, "max_price": 4000})
    assert "Blue Running Shoes Pro" in result


def test_search_products_by_size():
    result = search_products.invoke({"size": "12", "category": "footwear"})
    assert "Black Formal Leather Shoes" in result


def test_get_product_detail_exists():
    result = get_product_detail.invoke({"product_id": "P001"})
    assert "Classic Fit Red Running Shoes" in result
    assert "SportMax" in result
    assert "Rs.2999" in result


def test_get_product_detail_not_found():
    result = get_product_detail.invoke({"product_id": "P999"})
    assert "nahi mila" in result.lower() or "not found" in result.lower()


def test_get_product_detail_case_insensitive():
    result = get_product_detail.invoke({"product_id": "p007"})
    assert "Wireless Bluetooth Headphones" in result


def test_get_order_status_delivered():
    result = get_order_status.invoke({"order_id": "ORD456"})
    assert "Delivered" in result
    assert "Priya Patel" not in result


def test_get_order_status_shipped():
    result = get_order_status.invoke({"order_id": "ORD123"})
    assert "Shipped" in result
    assert "10 July" in result or "July 10" in result or "2026-07-10" in result


def test_get_order_status_not_found():
    result = get_order_status.invoke({"order_id": "ORD999"})
    assert "nahi mila" in result.lower() or "not found" in result.lower()


def test_get_order_status_failed_payment():
    result = get_order_status.invoke({"order_id": "ORD202"})
    assert "Shipped" in result
    assert "failed" in result.lower()


def test_get_active_offers_all():
    result = get_active_offers.invoke({})
    assert "SUMMER20" in result
    assert "FREESHIP" in result
    assert "WELCOME10" in result
    assert "FITNESS25" in result


def test_get_active_offers_by_category():
    result = get_active_offers.invoke({"category": "sports"})
    assert "FITNESS25" in result
    assert "SUMMER20" not in result


def test_get_active_offers_no_match():
    result = get_active_offers.invoke({"category": "automotive"})
    assert "FREESHIP" in result
    assert "WELCOME10" in result
    assert "SUMMER20" not in result


def test_get_product_reviews_existing():
    result = get_product_reviews.invoke({"product_id": "P001"})
    assert "Amit K." in result
    assert "Bahut comfortable" in result
    assert "Reviews" in result


def test_get_product_reviews_no_reviews():
    result = get_product_reviews.invoke({"product_id": "P999"})
    assert "nahi" in result.lower() or "no" in result.lower()


def test_get_return_policy_general():
    result = get_return_policy.invoke({})
    assert "15 days" in result or "return window" in result.lower()
    assert "condition" in result.lower()


def test_get_return_policy_by_category():
    result = get_return_policy.invoke({"category": "electronics"})
    assert "10 days" in result
    assert "Electronics" in result


def test_get_return_policy_invalid_category():
    result = get_return_policy.invoke({"category": "invalid"})
    assert "available nahi" in result.lower() or "not available" in result.lower()


def test_get_return_policy_no_return_category():
    result = get_return_policy.invoke({"category": "health"})
    assert "0 days" in result or "cannot be returned" in result or "hygiene" in result.lower()
