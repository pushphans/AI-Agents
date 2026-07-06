from langchain_core.tools import tool

from app.core.data_loader import (
    load_offers,
    load_orders,
    load_products,
    load_return_policy,
    load_reviews,
)


@tool
def search_products(
    color: str | None = None,
    size: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> str:
    """Search products by color, size, category, brand, or price range."""
    products = load_products()
    if color:
        products = [p for p in products if p["color"] == color.lower()]
    if size:
        products = [p for p in products if size in p.get("sizes", [])]
    if category:
        products = [p for p in products if p["category"] == category.lower()]
    if brand:
        products = [p for p in products if p["brand"].lower() == brand.lower()]
    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if not products:
        return "Koi product nahi mila."
    lines = [
        f"- {p['name']} - Rs.{p['price']} (rating: {p['rating']})" for p in products
    ]
    return "Ye products mile:\n" + "\n".join(lines)


@tool
def get_product_detail(product_id: str) -> str:
    """Get full details of a product by its ID (e.g. P001, P002)."""
    products = load_products()
    for p in products:
        if p["id"] == product_id.upper():
            return (
                f"{p['name']}\n"
                f"Brand: {p['brand']} | Category: {p['category']}\n"
                f"Color: {p['color']} | Sizes: {', '.join(p['sizes']) if p['sizes'] else 'N/A'}\n"
                f"Price: Rs.{p['price']} | Rating: {p['rating']}/5\n"
                f"Stock: {p['stock']}\n"
                f"{p['description']}"
            )
    return f"Product {product_id} nahi mila."


@tool
def get_order_status(order_id: str) -> str:
    """Get order status and tracking by order ID (e.g. ORD123)."""
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id.upper():
            items = ", ".join(i["name"] for i in o["items"])
            eta = o["eta"] or "N/A"
            trk = o["tracking"] or "Not yet assigned"
            return (
                f"Order {o['id']} - {o['status'].title()}\n"
                f"Items: {items}\n"
                f"Total: Rs.{o['total']}\n"
                f"Payment: {o['payment_status']}\n"
                f"ETA: {eta}\n"
                f"Tracking: {trk}\n"
                f"Address: {o['address']}"
            )
    return f"Order {order_id} nahi mila."


@tool
def get_active_offers(category: str | None = None) -> str:
    """Get active offers/discounts. Optionally filter by category (e.g. clothing, electronics)."""
    offers = load_offers()
    active = [o for o in offers if o.get("active")]
    if category:
        active = [
            o
            for o in active
            if o["category"] is None or o["category"] == category.lower()
        ]
    if not active:
        return "Abhi koi active offer nahi hai."
    lines = [f"- {o['code']}: {o['description']}" for o in active]
    return "Ye offers chal rahe hain:\n" + "\n".join(lines)


@tool
def get_product_reviews(product_id: str) -> str:
    """Get customer reviews for a product by its ID (e.g. P001)."""
    all_reviews = load_reviews()
    reviews = [r for r in all_reviews if r["product_id"] == product_id.upper()]
    if not reviews:
        return "Is product ke liye koi review nahi hai."
    lines = [f"- {r['user']} ({r['rating']}/5): {r['text']}" for r in reviews]
    return "Reviews:\n" + "\n".join(lines)


@tool
def get_return_policy(category: str | None = None) -> str:
    """Get return policy info. Optionally filter by product category."""
    policy = load_return_policy()
    gen = policy["general"]
    if not category:
        return (
            f"Return window: {gen['return_window_days']} days\n"
            f"Condition: {gen['condition']}\n"
            f"Process: {gen['process']}\n"
            f"Refund: {gen['refund_timeline']}\n"
            f"Exceptions: {', '.join(gen['exceptions'])}"
        )
    cat_info = policy["categories"].get(category.lower())
    if not cat_info:
        return f"'{category}' category ka return policy available nahi hai."
    return (
        f"{category.title()} - Return window: {cat_info['return_window_days']} days\n"
        f"Note: {cat_info['notes']}"
    )


TOOLS = [
    search_products,
    get_product_detail,
    get_order_status,
    get_active_offers,
    get_product_reviews,
    get_return_policy,
]
