import os
import sqlite3

from app.core.config import settings

USERS_DATA = [
    ("Amit Sharma", "amit@example.com", "2026-01-15", 1),
    ("Priya Patel", "priya@example.com", "2026-02-20", 1),
    ("Rahul Verma", "rahul@example.com", "2026-03-10", 1),
    ("Sneha Gupta", "sneha@example.com", "2026-04-05", 0),
    ("Vikram Singh", "vikram@example.com", "2026-05-12", 1),
    ("Neha Joshi", "neha@example.com", "2026-06-18", 1),
    ("Arjun Mehta", "arjun@example.com", "2026-01-22", 1),
    ("Kavita Reddy", "kavita@example.com", "2026-02-28", 0),
    ("Rohit Nair", "rohit@example.com", "2026-03-15", 1),
    ("Ananya Das", "ananya@example.com", "2026-04-30", 1),
]

ORDERS_DATA = [
    (1, "Laptop", 54999.00, "2026-06-01", "delivered"),
    (1, "Mouse", 799.00, "2026-06-15", "delivered"),
    (2, "Keyboard", 2499.00, "2026-06-10", "shipped"),
    (2, "Monitor", 18999.00, "2026-06-20", "pending"),
    (3, "Headphones", 3499.00, "2026-06-05", "delivered"),
    (4, "Webcam", 4999.00, "2026-06-12", "cancelled"),
    (5, "Laptop", 62999.00, "2026-06-18", "shipped"),
    (6, "Tablet", 29999.00, "2026-06-22", "pending"),
    (7, "Phone Case", 599.00, "2026-06-25", "delivered"),
    (8, "Charger", 1299.00, "2026-06-28", "shipped"),
    (9, "Earbuds", 1999.00, "2026-07-01", "pending"),
    (10, "Smartwatch", 14999.00, "2026-07-03", "delivered"),
    (3, "USB Cable", 399.00, "2026-07-05", "shipped"),
    (1, "Stand", 1899.00, "2026-07-06", "pending"),
    (5, "Mousepad", 499.00, "2026-07-06", "delivered"),
]

PRODUCTS_DATA = [
    ("Laptop", "Electronics", 54999.00, 25),
    ("Mouse", "Accessories", 799.00, 150),
    ("Keyboard", "Accessories", 2499.00, 80),
    ("Monitor", "Electronics", 18999.00, 40),
    ("Headphones", "Audio", 3499.00, 60),
    ("Webcam", "Electronics", 4999.00, 35),
    ("Tablet", "Electronics", 29999.00, 20),
    ("Smartwatch", "Wearables", 14999.00, 45),
]


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    amount REAL NOT NULL,
    order_date DATE NOT NULL,
    status TEXT CHECK(status IN ('pending', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_users_signup_date ON users(signup_date);",
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
]


def create_database() -> sqlite3.Connection:
    db_exists = os.path.exists(settings.DB_PATH)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if not db_exists:
        cursor.executescript(CREATE_TABLES_SQL)

        cursor.executemany(
            "INSERT INTO users (name, email, signup_date, is_active) VALUES (?, ?, ?, ?)",
            USERS_DATA,
        )
        cursor.executemany(
            "INSERT INTO orders (user_id, product_name, amount, order_date, status) VALUES (?, ?, ?, ?, ?)",
            ORDERS_DATA,
        )
        cursor.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            PRODUCTS_DATA,
        )

        for idx_sql in CREATE_INDEXES_SQL:
            cursor.execute(idx_sql)

        conn.commit()
        print(f"[DB] Created data.db at {settings.DB_PATH} with seed data.")
    else:
        print(f"[DB] Connected to existing data.db at {settings.DB_PATH}.")

    return conn


def get_schema_string() -> str:
    return """
TABLE: users
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  name        TEXT NOT NULL
  email       TEXT UNIQUE NOT NULL
  signup_date DATE NOT NULL
  is_active   BOOLEAN DEFAULT 1

TABLE: orders
  id            INTEGER PRIMARY KEY AUTOINCREMENT
  user_id       INTEGER NOT NULL (FK -> users.id)
  product_name  TEXT NOT NULL
  amount        REAL NOT NULL
  order_date    DATE NOT NULL
  status        TEXT CHECK IN ('pending','shipped','delivered','cancelled')

TABLE: products
  id        INTEGER PRIMARY KEY AUTOINCREMENT
  name      TEXT NOT NULL
  category  TEXT NOT NULL
  price     REAL NOT NULL
  stock     INTEGER DEFAULT 0
"""


def get_schema_for_prompt() -> str:
    return get_schema_string().strip()


def reset_database() -> sqlite3.Connection:
    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
    return create_database()
