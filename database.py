import os
import sqlite3
import ast
from datetime import datetime
from Graphite import GraphiteInter

import sys

if os.environ.get('VERCEL') == '1':
    base_dir = '/tmp'
elif hasattr(sys, '_MEIPASS'):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(base_dir, "kiosk.db")
INI_FILE = os.path.join(base_dir, "Bridge.ini")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database and inserts default products if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table: Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # 2. Table: Cart
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            product_code TEXT PRIMARY KEY,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            FOREIGN KEY (product_code) REFERENCES products (code) ON DELETE CASCADE
        )
    """)
    
    # 3. Table: Sales History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    
    # 4. Table: Access Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            ip TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # 5. Table: Used Receipts (Double-Spending prevention)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # Seed default products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("100", "Doce de Leite", "Sobremesas", 12.90, "1zYZMU.png", "Delicioso doce de leite artesanal tradicional mineiro."),
            ("101", "Chocolate Barra", "Sobremesas", 8.50, "1zYZMU.png", "Barra de chocolate ao leite cremosa e macia de 100g."),
            ("102", "Pão de Queijo", "Lanches", 4.50, "1zYZMU.png", "Pão de queijo mineiro quentinho, crocante por fora e macio por dentro."),
            ("103", "Café Expresso", "Bebidas", 6.00, "1zYZMU.png", "Café expresso encorpado preparado na hora com grãos nobres selecionados."),
            ("104", "Refrigerante", "Bebidas", 7.00, "1zYZMU.png", "Lata de refrigerante geladinho (350ml) para acompanhar sua refeição."),
            ("105", "Água Mineral", "Bebidas", 3.00, "1zYZMU.png", "Garrafa de água mineral pura e refrescante de 500ml.")
        ]
        cursor.executemany("""
            INSERT INTO products (code, name, category, price, image, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, default_products)
        conn.commit()
        print("[Database] Seed default products inserted successfully.")
        
    conn.close()

# ── Dual-Write Bridge.ini Sync Layer ───────────────────────────────────────

def sync_cart_to_ini():
    """Fetches active SQLite cart and writes to legacy Bridge.ini file for external integration."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get cart items with prices
        cursor.execute("""
            SELECT c.product_code, c.quantity, p.price 
            FROM cart c 
            JOIN products p ON c.product_code = p.code
        """)
        rows = cursor.fetchall()
        
        cart_list = []
        total = 0.0
        
        for r in rows:
            code = r["product_code"]
            qty = r["quantity"]
            price = r["price"]
            
            cart_list.append({"codigo": code, "quantidade": qty})
            total += price * qty
            
        conn.close()
        
        total = round(total, 2)
        
        # Write to INI using existing GraphiteInter class
        GraphiteInter.Change_ini(INI_FILE, "Carrinho", "carrinho", str(cart_list))
        GraphiteInter.Change_ini(INI_FILE, "Pagamento", "total", str(total))
        
        print(f"[Sync] Cart synced to INI. Total: {total}. Items: {len(cart_list)}")
        return total
    except Exception as e:
        print(f"[Sync] Error syncing cart to INI: {e}")
        return 0.0

# ── Cart DB Managers ────────────────────────────────────────────────────────

def get_cart_items():
    """Gets detailed cart items with product details and subtotal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.product_code AS code, p.name, p.price, p.image, c.quantity 
        FROM cart c 
        JOIN products p ON c.product_code = p.code
    """)
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    subtotal = 0.0
    for r in rows:
        item_sub = round(r["price"] * r["quantity"], 2)
        subtotal += item_sub
        items.append({
            "code": r["code"],
            "name": r["name"],
            "price": r["price"],
            "image": r["image"],
            "quantity": r["quantity"],
            "subtotal": item_sub
        })
        
    return {
        "items": items,
        "total": round(subtotal, 2)
    }

def add_product_to_cart(code):
    """Adds or increments a product in the SQLite cart and triggers INI sync."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify product exists
    cursor.execute("SELECT 1 FROM products WHERE code = ?", (code,))
    if not cursor.fetchone():
        conn.close()
        return False, "Produto não encontrado!"
        
    # Check if already in cart
    cursor.execute("SELECT quantity FROM cart WHERE product_code = ?", (code,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE product_code = ?", (code,))
    else:
        cursor.execute("INSERT INTO cart (product_code, quantity) VALUES (?, 1)", (code,))
        
    conn.commit()
    conn.close()
    
    sync_cart_to_ini()
    return True, "Produto adicionado ao carrinho!"

def update_cart_quantity(code, qty):
    """Updates a product's quantity in the SQLite cart, or deletes it if qty < 1."""
    if qty < 1:
        return remove_from_cart(code)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cart SET quantity = ? WHERE product_code = ?", (qty, code))
    conn.commit()
    conn.close()
    
    sync_cart_to_ini()
    return True

def remove_from_cart(code):
    """Removes a product from the SQLite cart and triggers INI sync."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE product_code = ?", (code,))
    conn.commit()
    conn.close()
    
    sync_cart_to_ini()
    return True

def clear_cart():
    """Clears the SQLite cart and triggers INI sync."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart")
    conn.commit()
    conn.close()
    
    sync_cart_to_ini()
    return True

# ── Products DB Managers ──────────────────────────────────────────────────

def get_all_products():
    """Gets all products from catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]

def get_product(code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_product(code, name, category, price, image="1zYZMU.png", description=""):
    """Inserts or updates a product in the catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (code, name, category, price, image, description)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name=excluded.name,
            category=excluded.category,
            price=excluded.price,
            image=excluded.image,
            description=excluded.description
    """, (code, name, category, float(price), image, description))
    conn.commit()
    conn.close()
    return True

def delete_product(code):
    """Deletes a product from the catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    return True

# ── Sales & Logs DB Managers ──────────────────────────────────────────────

def log_sale(payment_method, subtotal, tax, total, status="Aprovado"):
    """Logs a successful transaction in sales history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO sales (timestamp, payment_method, subtotal, tax, total, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, payment_method, float(subtotal), float(tax), float(total), status))
    conn.commit()
    conn.close()
    return True

def log_access(path, ip):
    """Logs route access with client IP and timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    cursor.execute("""
        INSERT INTO access_logs (path, ip, timestamp)
        VALUES (?, ?, ?)
    """, (path, ip, timestamp))
    conn.commit()
    conn.close()
    return True

def get_sales_history():
    """Gets all sales recorded."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_access_logs():
    """Gets recent access logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT 150")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_sales_stats():
    """Fetches high-level stats for the admin dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total revenue
    cursor.execute("SELECT SUM(total) FROM sales WHERE status='Aprovado'")
    revenue = cursor.fetchone()[0] or 0.0
    
    # 2. Total order count
    cursor.execute("SELECT COUNT(*) FROM sales WHERE status='Aprovado'")
    orders_count = cursor.fetchone()[0] or 0
    
    # 3. Revenue by payment method
    cursor.execute("""
        SELECT payment_method, SUM(total) as val 
        FROM sales 
        WHERE status='Aprovado' 
        GROUP BY payment_method
    """)
    by_method = {row["payment_method"]: row["val"] for row in cursor.fetchall()}
    
    # 4. Total products catalog count
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0] or 0
    
    conn.close()
    
    # Round metrics
    revenue = round(revenue, 2)
    ticket = round(revenue / orders_count, 2) if orders_count > 0 else 0.0
    
    return {
        "revenue": revenue,
        "orders_count": orders_count,
        "ticket": ticket,
        "by_method": by_method,
        "products_count": products_count
    }

def is_receipt_used(tx_id):
    """Checks if a PIX transaction ID (E2E ID) has already been used for a sale."""
    if not tx_id:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM used_receipts WHERE transaction_id = ?", (tx_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def register_receipt(tx_id):
    """Registers a PIX transaction ID (E2E ID) to prevent it from being used again."""
    if not tx_id:
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT OR IGNORE INTO used_receipts (transaction_id, timestamp)
            VALUES (?, ?)
        """, (tx_id.strip(), timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error registering receipt: {e}")
        return False

# Initialize DB on load to guarantee file existence
init_db()
