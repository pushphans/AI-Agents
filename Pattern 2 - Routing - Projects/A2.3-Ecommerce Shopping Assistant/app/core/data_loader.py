import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load(filename: str) -> list | dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def load_products() -> list[dict]:
    return _load("products.json")


def load_orders() -> list[dict]:
    return _load("orders.json")


def load_offers() -> list[dict]:
    return _load("offers.json")


def load_reviews() -> list[dict]:
    return _load("reviews.json")


def load_return_policy() -> dict:
    return _load("return_policy.json")
