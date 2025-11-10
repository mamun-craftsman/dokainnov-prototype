"""
Check what forecasts exist in the database
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "database" / "dokainnov.db"

print(f"Checking database: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}\n")

if not DB_PATH.exists():
    print("[ERROR] Database not found!")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Check table structure
print("=" * 70)
print("TABLE STRUCTURE")
print("=" * 70)
cursor.execute("PRAGMA table_info(product_forecasts)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else ''}")

# Count total forecasts
print("\n" + "=" * 70)
print("FORECAST STATISTICS")
print("=" * 70)
cursor.execute("SELECT COUNT(*) FROM product_forecasts")
total = cursor.fetchone()[0]
print(f"Total forecasts: {total}")

if total > 0:
    # Get date range
    cursor.execute("SELECT MIN(forecast_date), MAX(forecast_date) FROM product_forecasts")
    min_date, max_date = cursor.fetchone()
    print(f"Date range: {min_date} to {max_date}")
    
    # Count by product
    cursor.execute("""
        SELECT product_id, COUNT(*) as count
        FROM product_forecasts
        GROUP BY product_id
        ORDER BY count DESC
        LIMIT 10
    """)
    print("\nTop 10 products with most forecasts:")
    for row in cursor.fetchall():
        print(f"  Product {row[0]}: {row[1]} forecasts")
    
    # Show latest 10
    print("\n" + "=" * 70)
    print("LATEST 10 FORECASTS")
    print("=" * 70)
    cursor.execute("""
        SELECT 
            pf.id,
            pf.product_id,
            p.product_name,
            pf.forecast_date,
            pf.forecast_qty,
            pf.expected_profit,
            SUBSTR(pf.ai_advice, 1, 60) as advice_preview
        FROM product_forecasts pf
        LEFT JOIN products p ON pf.product_id = p.product_id
        ORDER BY pf.id DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"\nID: {row[0]} | Product {row[1]}: {row[2]}")
        print(f"  Date: {row[3]}")
        print(f"  Qty: {row[4]:.1f} | Profit: ৳{row[5]:,.0f}")
        print(f"  Advice: {row[6]}...")
else:
    print("\n[INFO] No forecasts found in database")
    print("This means ai_advisor.py hasn't successfully saved any data yet")

conn.close()

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
