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
    
    # 6. Table: Settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # Seed default settings if table is empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ("pix_key", "00020126580014br.gov.bcb.pix0136e054cfdf-e2a2-4a7b-a010-38435d100096520400005303986540510.005802BR5915TerminalPDV6009SaoPaulo62070503***6304A2B8"),
            ("pix_receiver", "Ednilson Cesar Nery"),
            ("pix_bank", "Banco do Brasil")
        ]
        cursor.executemany("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
        """, default_settings)
        conn.commit()
        print("[Database] Default settings inserted successfully.")
    
    # Seed default products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("100", "Doce de Leite", "Sobremesas", 12.90, "https://drive.google.com/file/d/1oNYgYYTiAFx9dHqJpK_gWCMlSosiTYxY/view?usp=drive_link", "Delicioso doce de leite artesanal tradicional mineiro."),
            ("101", "Chocolate Barra", "Sobremesas", 8.50, "https://drive.google.com/file/d/1fp-U83TPoQYfcHbozQsDPVq8xgYZjAq1/view?usp=drive_link", "Barra de chocolate ao leite cremosa e macia de 100g."),
            ("102", "Pão de Queijo", "Lanches", 4.50, "https://drive.google.com/file/d/1vsMtQxgeEUn_gVcXNKQNKCQEZzzvyBZG/view?usp=drive_link", "Pão de queijo mineiro quentinho, crocante por fora e macio por dentro."),
            ("103", "Café Expresso", "Bebidas", 6.00, "https://drive.google.com/file/d/1Y8F4NWJkcfVnXrS61Cnk-9dyR-jOJBDa/view?usp=drive_link", "Café expresso encorpado preparado na hora com grãos nobres selecionados."),
            ("104", "Refrigerante", "Bebidas", 7.00, "https://drive.google.com/file/d/1ivQFUCgV16SjpjycYDEHUB5xOimeGTV4/view?usp=drive_link", "Lata de refrigerante geladinho (350ml) para acompanhar sua refeição."),
            ("105", "Água Mineral", "Bebidas", 3.00, "https://drive.google.com/file/d/1gFN4PjE4La4u6C5Cg-rIQIUV45Lw5kH_/view?usp=drive_link", "Garrafa de água mineral pura e refrescante de 500ml."),
            ("152", "Misto Quente", "Lanches", 12.00, "https://drive.google.com/file/d/1irI7zvIHn1QdXZhBhppYe2L90iXVZONP/view?usp=drive_link", ""),
            ("237", "Brownie", "Sobremesas", 10.00, "https://drive.google.com/file/d/1WdPVxDL4EVS5c6unvDT3P9cDi8NNivl5/view?usp=drive_link", "Brownie Koda"),
            ("300", "Pão francês", "Pães", 1.50, "1zYZMU.png", "Pão francês fresquinho e crocante."),
            ("301", "Pão de leite", "Pães", 2.50, "1zYZMU.png", "Pão de leite macio e saboroso."),
            ("302", "Pão integral", "Pães", 4.50, "1zYZMU.png", "Pão integral rico em fibras."),
            ("303", "Pão de forma", "Pães", 8.00, "1zYZMU.png", "Pão de forma tradicional fatiado."),
            ("304", "Pão australiano", "Pães", 6.00, "1zYZMU.png", "Pão australiano escuro e levemente adocicado."),
            ("305", "Baguete", "Pães", 20.00, "1zYZMU.png", "Baguete tradicional crocante."),
            ("306", "Bisnaga", "Pães", 3.00, "1zYZMU.png", "Bisnaga macia, ideal para lanches."),
            ("307", "Croissant", "Pães", 11.50, "1zYZMU.png", "Croissant folhado amanteigado."),
            ("308", "Bolo de chocolate", "Bolos e Tortas", 30.00, "1zYZMU.png", "Bolo de chocolate com cobertura."),
            ("309", "Bolo de cenoura", "Bolos e Tortas", 30.00, "1zYZMU.png", "Bolo de cenoura com calda de chocolate."),
            ("310", "Bolo de fubá", "Bolos e Tortas", 22.00, "1zYZMU.png", "Bolo de fubá caseiro tradicional."),
            ("311", "Bolo de milho", "Bolos e Tortas", 25.00, "1zYZMU.png", "Bolo de milho cremoso irresistível."),
            ("312", "Torta de frango", "Bolos e Tortas", 8.50, "1zYZMU.png", "Torta salgada de frango desfiado temperado."),
            ("313", "Torta de palmito", "Bolos e Tortas", 12.00, "1zYZMU.png", "Torta salgada com recheio cremoso de palmito."),
            ("314", "Cheesecake", "Bolos e Tortas", 14.00, "1zYZMU.png", "Cheesecake clássica com calda de frutas vermelhas."),
            ("315", "Rocambole", "Bolos e Tortas", 20.00, "1zYZMU.png", "Rocambole doce recheado."),
            ("316", "Coxinha", "Salgados", 11.50, "1zYZMU.png", "Coxinha de frango frita na hora."),
            ("317", "Esfiha", "Salgados", 11.50, "1zYZMU.png", "Esfiha assada de carne ou queijo."),
            ("318", "Empada", "Salgados", 11.50, "1zYZMU.png", "Empada de frango ou palmito massa podre."),
            ("319", "Pastel", "Salgados", 18.00, "1zYZMU.png", "Pastel frito super crocante."),
            ("320", "Quibe", "Salgados", 11.50, "1zYZMU.png", "Quibe frito tradicional temperado com hortelã."),
            ("321", "Enroladinho de salsicha", "Salgados", 5.50, "1zYZMU.png", "Enroladinho de salsicha assado e macio."),
            ("322", "Pão de batata", "Salgados", 6.50, "1zYZMU.png", "Pão de batata macio com requeijão."),
            ("323", "Risole", "Salgados", 11.50, "1zYZMU.png", "Risole frito com recheio cremoso."),
            ("324", "Brigadeiro", "Doces", 8.00, "1zYZMU.png", "Brigadeiro de chocolate gourmet com granulado."),
            ("325", "Beijinho", "Doces", 8.00, "1zYZMU.png", "Doce de coco tradicional com cravo."),
            ("326", "Sonho", "Doces", 10.00, "1zYZMU.png", "Sonho tradicional recheado com creme de confeiteiro."),
            ("327", "Carolinas", "Doces", 8.00, "1zYZMU.png", "Carolinas recheadas com doce de leite e cobertura de chocolate."),
            ("328", "Bombom", "Doces", 4.00, "1zYZMU.png", "Bombom artesanal de sabores variados."),
            ("329", "Pudim", "Doces", 14.00, "1zYZMU.png", "Fatia de pudim de leite condensado super cremoso."),
            ("330", "Quindim", "Doces", 9.00, "1zYZMU.png", "Quindim tradicional brilhante e saboroso."),
            ("331", "Cookie", "Doces", 12.00, "1zYZMU.png", "Cookie com gotas de chocolate crocante por fora e macio por dentro."),
            ("332", "Presunto", "Frios e Laticínios", 6.00, "1zYZMU.png", "Fatias finas de presunto cozido (100g)."),
            ("333", "Queijo muçarela", "Frios e Laticínios", 37.00, "1zYZMU.png", "Fatias de queijo muçarela fresco e derretível (100g)."),
            ("334", "Queijo prato", "Frios e Laticínios", 35.90, "1zYZMU.png", "Fatias de queijo prato fatiado (100g)."),
            ("335", "Requeijão", "Frios e Laticínios", 8.50, "1zYZMU.png", "Copo de requeijão cremoso tradicional (200g)."),
            ("336", "Manteiga", "Frios e Laticínios", 9.00, "1zYZMU.png", "Manteiga com sal de primeira qualidade (200g)."),
            ("337", "Cream cheese", "Frios e Laticínios", 10.00, "1zYZMU.png", "Cream cheese cremoso e suave (150g)."),
            ("338", "Iogurte", "Frios e Laticínios", 5.00, "1zYZMU.png", "Iogurte natural ou de frutas refrescante."),
            ("339", "Café com leite", "Bebidas", 8.00, "1zYZMU.png", "Café com leite quentinho e equilibrado."),
            ("340", "Cappuccino", "Bebidas", 8.00, "1zYZMU.png", "Cappuccino cremoso com chocolate e canela."),
            ("341", "Chocolate quente", "Bebidas", 8.00, "1zYZMU.png", "Chocolate quente cremoso e aconchegante."),
            ("342", "Suco natural", "Bebidas", 9.00, "1zYZMU.png", "Suco natural feito com frutas frescas da época."),
            ("343", "Energético", "Bebidas", 10.00, "1zYZMU.png", "Lata de energético gelado para dar um up."),
            ("344", "Rosquinha", "Biscoitos e Snacks", 5.00, "1zYZMU.png", "Pacote de rosquinhas crocantes doces."),
            ("345", "Torrada", "Biscoitos e Snacks", 4.50, "1zYZMU.png", "Torradas crocantes tradicionais."),
            ("346", "Biscoito amanteigado", "Biscoitos e Snacks", 6.00, "1zYZMU.png", "Biscoito amanteigado derrete na boca."),
            ("347", "Bolacha recheada", "Biscoitos e Snacks", 4.00, "1zYZMU.png", "Pacote de bolacha recheada sabor chocolate ou morango."),
            ("348", "Salgadinho", "Biscoitos e Snacks", 5.00, "1zYZMU.png", "Pacote de salgadinho de milho ou batata."),
            ("349", "Amendoim", "Biscoitos e Snacks", 5.00, "1zYZMU.png", "Pacote de amendoim torrado e salgado.")
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

def get_setting(key, default_value=""):
    """Gets a setting value from settings table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else default_value
    except Exception as e:
        print(f"[Database] Error reading setting '{key}': {e}")
        return default_value

def set_setting(key, value):
    """Sets/updates a setting value in settings table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error writing setting '{key}': {e}")
        return False

# Initialize DB on load to guarantee file existence
init_db()
