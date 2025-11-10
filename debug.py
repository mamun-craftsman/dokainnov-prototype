import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

JSON_PATH = Path(__file__).parent.parent / "dokainnov_ml_engine" / "data" / "ai_recommendations.json"
CSV_PATH = Path(__file__).parent.parent / "dokainnov_ml_engine" / "data" / "forecast_output.csv"
DB_PATH = Path(__file__).parent / "database" / "dokainnov.db"

print("="*70)
print("SAVE JSON+CSV TO DATABASE")
print("="*70)

if not JSON_PATH.exists():
    print("[ERROR] JSON not found!")
    exit(1)

if not CSV_PATH.exists():
    print("[ERROR] CSV not found!")
    exit(1)

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    ai_data = json.load(f)

print(f"\n[JSON] {len(ai_data.get('products', []))} recommendations")
print("Product IDs in JSON:")
for p in ai_data.get('products', []):
    print(f"  - {p['product_id']}")

forecast_df = pd.read_csv(CSV_PATH)
print(f"\n[CSV] {len(forecast_df)} rows")

weekly_forecast = forecast_df.groupby('product_id').agg({
    'forecast_qty': 'sum',
    'cost_price': 'first',
    'unit_price': 'first'
}).reset_index()

print(f"[CSV] {len(weekly_forecast)} unique products")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("\n[DB] Checking products table structure...")
cursor.execute("PRAGMA table_info(products)")
cols = cursor.fetchall()
print("Columns:")
for col in cols:
    print(f"  - {col[1]}")

stock_col = None
for col in cols:
    if 'stock' in col[1].lower():
        stock_col = col[1]
        break

if not stock_col:
    print("\n[WARN] No stock column found, using 0 for all")
    stock_dict = {}
else:
    print(f"\n[DB] Using column: {stock_col}")
    cursor.execute(f"SELECT product_id, {stock_col} FROM products")
    stock_dict = dict(cursor.fetchall())

print("\n[INSERT] Starting inserts...")
inserted = 0

for ai_rec in ai_data.get('products', []):
    try:
        pid = int(ai_rec['product_id'])
        advice = ai_rec.get('advice', 'No advice')
        
        forecast_row = weekly_forecast[weekly_forecast['product_id'] == pid]
        
        if forecast_row.empty:
            print(f"[SKIP] Product {pid}: Not in CSV")
            continue
        
        qty = float(forecast_row['forecast_qty'].iloc[0])
        cost = float(forecast_row['cost_price'].iloc[0])
        price = float(forecast_row['unit_price'].iloc[0])
        
        profit_per_unit = price - cost
        expected_profit = qty * profit_per_unit
        
        stock = stock_dict.get(pid, 0)
        reorder = max(0, qty - stock)
        
        forecast_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO product_forecasts 
            (product_id, forecast_date, forecast_qty, expected_profit, reorder_needed, ai_advice)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, forecast_date, qty, expected_profit, reorder, advice))
        
        inserted += 1
        print(f"[OK] Product {pid}: {qty:.1f} units, Tk{expected_profit:.0f}")
        
    except Exception as e:
        print(f"[ERROR] Product {ai_rec.get('product_id')}: {e}")
        import traceback
        traceback.print_exc()

conn.commit()

cursor.execute("SELECT COUNT(*) FROM product_forecasts")
total = cursor.fetchone()[0]

conn.close()

print(f"\n{'='*70}")
print(f"Inserted: {inserted}")
print(f"Total in DB: {total}")
print(f"{'='*70}")
