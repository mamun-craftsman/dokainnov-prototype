import sqlite3
import shutil
from datetime import datetime

# Backup old database
shutil.copy('database/dokainnov.db', f'database/dokainnov_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
print("✅ Backup created")

conn = sqlite3.connect('database/dokainnov.db')
cursor = conn.cursor()

# Check if old sales table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
if cursor.fetchone():
    print("📋 Old sales table found, dropping...")
    cursor.execute('DROP TABLE IF EXISTS sales')
    cursor.execute('DROP TABLE IF EXISTS sale_items')
    cursor.execute('DROP TABLE IF EXISTS customers')

# Create new tables
print("🔧 Creating new sales schema...")

cursor.execute('''
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT,
        sale_date DATE NOT NULL,
        total_amount REAL NOT NULL,
        discount REAL DEFAULT 0,
        final_amount REAL NOT NULL,
        paid_amount REAL NOT NULL,
        due_amount REAL DEFAULT 0,
        payment_status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE sale_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        sale_date DATE NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
''')

cursor.execute('''
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT UNIQUE NOT NULL,
        customer_phone TEXT,
        total_purchases REAL DEFAULT 0,
        purchase_count INTEGER DEFAULT 0,
        last_purchase_date DATE,
        segment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("✅ Migration complete! Products preserved, sales schema updated.")
print("   You can now run: streamlit run Home.py")
