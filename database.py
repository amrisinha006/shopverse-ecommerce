import sqlite3
import hashlib
import secrets
from pathlib import Path

DB_PATH = Path(__file__).parent / "shopverse.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    ).hex()

    return f"{salt}${hashed}"


def verify_password(password, stored):
    try:
        salt, original_hash = stored.split("$")

        new_hash = hash_password(password, salt).split("$")[1]

        return secrets.compare_digest(
            original_hash,
            new_hash
        )
    except Exception:
        return False


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            image_url TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            payment_method TEXT DEFAULT 'COD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, product_id)
        )
    """)

    conn.commit()

    # Insert demo products only when the catalog is empty.
    cur.execute("SELECT COUNT(*) FROM products")

    if cur.fetchone()[0] == 0:
        products = [
            (
                "Wireless Headphones",
                "Comfortable wireless headphones with rich sound.",
                "Electronics",
                1499,
                20,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
            ),
            (
                "Smart Watch",
                "Smart watch with fitness tracking and notifications.",
                "Electronics",
                2499,
                15,
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30"
            ),
            (
                "Running Shoes",
                "Lightweight shoes for everyday running.",
                "Fashion",
                1999,
                25,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff"
            ),
            (
                "Backpack",
                "Durable backpack for college and travel.",
                "Accessories",
                999,
                30,
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"
            ),
            (
                "Sunglasses",
                "Modern sunglasses with UV protection.",
                "Fashion",
                799,
                18,
                "https://images.unsplash.com/photo-1511499767150-a48a237f0083"
            ),
            (
                "Coffee Mug",
                "Minimal ceramic coffee mug.",
                "Home",
                399,
                40,
                "https://images.unsplash.com/photo-1511920170033-f8396924c348"
            )
        ]

        cur.executemany("""
            INSERT INTO products
            (name, description, category, price, stock, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, products)

    conn.commit()
    conn.close()


def get_products(search="", category="All"):
    conn = get_connection()

    query = """
        SELECT * FROM products
        WHERE active = 1
    """

    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if category != "All":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"

    products = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return products


def get_product(product_id):
    conn = get_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    conn.close()

    return product


def get_categories():
    conn = get_connection()

    rows = conn.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE active = 1
    """).fetchall()

    conn.close()

    return ["All"] + [
        row["category"]
        for row in rows
    ]


def add_product(name, description, category, price,
                stock, image_url):
    conn = get_connection()

    conn.execute("""
        INSERT INTO products
        (name, description, category, price, stock, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        description,
        category,
        price,
        stock,
        image_url
    ))

    conn.commit()
    conn.close()


def update_product(product_id, name, description,
                   category, price, stock, image_url):
    conn = get_connection()

    conn.execute("""
        UPDATE products
        SET name = ?,
            description = ?,
            category = ?,
            price = ?,
            stock = ?,
            image_url = ?
        WHERE id = ?
    """, (
        name,
        description,
        category,
        price,
        stock,
        image_url,
        product_id
    ))

    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()

    conn.execute("""
        UPDATE products
        SET active = 0
        WHERE id = ?
    """, (product_id,))

    conn.commit()
    conn.close()


def register_user(name, email, password):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            name,
            email.lower(),
            hash_password(password)
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def login_user(email, password):
    conn = get_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE email = ?
    """, (email.lower(),)).fetchone()

    conn.close()

    if user and verify_password(
        password,
        user["password"]
    ):
        return user

    return None


def add_to_cart(user_id, product_id, quantity=1):
    conn = get_connection()

    product = conn.execute("""
        SELECT stock FROM products
        WHERE id = ? AND active = 1
    """, (product_id,)).fetchone()

    if not product or product["stock"] < quantity:
        conn.close()
        return False

    conn.execute("""
        INSERT INTO cart
        (user_id, product_id, quantity)
        VALUES (?, ?, ?)

        ON CONFLICT(user_id, product_id)
        DO UPDATE SET quantity =
            MIN(quantity + excluded.quantity,
                (SELECT stock FROM products
                 WHERE id = excluded.product_id))
    """, (
        user_id,
        product_id,
        quantity
    ))

    conn.commit()
    conn.close()

    return True


def get_cart(user_id):
    conn = get_connection()

    items = conn.execute("""
        SELECT
            products.id,
            products.name,
            products.price,
            products.stock,
            products.image_url,
            cart.quantity,
            products.price * cart.quantity AS subtotal

        FROM cart

        JOIN products
        ON cart.product_id = products.id

        WHERE cart.user_id = ?
        AND products.active = 1
    """, (user_id,)).fetchall()

    conn.close()

    return items


def update_cart_quantity(user_id, product_id, quantity):
    conn = get_connection()

    product = conn.execute("""
        SELECT stock FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if not product:
        conn.close()
        return

    if quantity <= 0:
        conn.execute("""
            DELETE FROM cart
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))

    else:
        quantity = min(quantity, product["stock"])

        conn.execute("""
            UPDATE cart
            SET quantity = ?
            WHERE user_id = ? AND product_id = ?
        """, (
            quantity,
            user_id,
            product_id
        ))

    conn.commit()
    conn.close()


def checkout(user_id, customer_name, address,
             phone, payment_method="COD"):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        items = conn.execute("""
            SELECT
                products.id,
                products.name,
                products.price,
                products.stock,
                cart.quantity

            FROM cart

            JOIN products
            ON cart.product_id = products.id

            WHERE cart.user_id = ?
            AND products.active = 1
        """, (user_id,)).fetchall()

        if not items:
            conn.rollback()
            return None

        total = sum(
            item["price"] * item["quantity"]
            for item in items
        )

        for item in items:
            if item["quantity"] > item["stock"]:
                conn.rollback()
                return None

        cursor = conn.execute("""
            INSERT INTO orders
            (user_id, customer_name, address,
             phone, total, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            customer_name,
            address,
            phone,
            total,
            payment_method
        ))

        order_id = cursor.lastrowid

        for item in items:
            conn.execute("""
                INSERT INTO order_items
                (order_id, product_id,
                 product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                item["id"],
                item["name"],
                item["price"],
                item["quantity"]
            ))

            conn.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                item["quantity"],
                item["id"]
            ))

        conn.execute("""
            DELETE FROM cart
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()

        return order_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_user_orders(user_id):
    conn = get_connection()

    orders = conn.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return orders


def get_order_items(order_id):
    conn = get_connection()

    items = conn.execute("""
        SELECT * FROM order_items
        WHERE order_id = ?
    """, (order_id,)).fetchall()

    conn.close()

    return items


def get_all_orders():
    conn = get_connection()

    orders = conn.execute("""
        SELECT * FROM orders
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return orders


def update_order_status(order_id, status):
    conn = get_connection()

    conn.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (status, order_id))

    conn.commit()
    conn.close()


def get_sales_summary():
    conn = get_connection()

    result = conn.execute("""
        SELECT
            COUNT(*) AS total_orders,
            COALESCE(SUM(total), 0) AS revenue
        FROM orders
    """).fetchone()

    conn.close()

    return result