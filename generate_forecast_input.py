import pandas as pd
import sqlite3
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    
DB_PATH = "database/dokainnov.db"
OUTPUT_PATH = "../dokainnov_ml_engine/data/predict_input.csv"

# Forecast horizon
forecast_days = 7
today = datetime.now().date()
forecast_dates = [today + timedelta(days=i) for i in range(1, forecast_days + 1)]

# Festival dates for 2025
eid_al_fitr_2025 = datetime(2025, 3, 30).date()
eid_al_adha_2025 = datetime(2025, 6, 7).date()
durga_puja_start_2025 = datetime(2025, 10, 2).date()
durga_puja_end_2025 = datetime(2025, 10, 6).date()
pohela_boishakh_2025 = datetime(2025, 4, 14).date()

def label_festival(day):
    labels = []
    if eid_al_fitr_2025 - timedelta(days=3) <= day <= eid_al_fitr_2025 + timedelta(days=3):
        labels.append("eid_fitr")
    if eid_al_adha_2025 - timedelta(days=4) <= day <= eid_al_adha_2025 + timedelta(days=6):
        labels.append("eid_adha")
    if durga_puja_start_2025 <= day <= durga_puja_end_2025:
        labels.append("durga_puja")
    if abs((day - pohela_boishakh_2025).days) <= 2:
        labels.append("pohela_boishakh")
    return ",".join(labels) if labels else "none"

def days_to_next_fest(day):
    fest_days = [
        (eid_al_fitr_2025 - day).days,
        (eid_al_adha_2025 - day).days,
        (durga_puja_start_2025 - day).days,
        (pohela_boishakh_2025 - day).days,
    ]
    fest_days = [d for d in fest_days if d >= 0]
    return min(fest_days) if fest_days else -1

# Load product info
conn = sqlite3.connect(DB_PATH)
products_df = pd.read_sql_query("SELECT product_id, category, cost_price, selling_price, unit FROM products", conn)
conn.close()

# Build forecast rows
rows = []
for _, prod in products_df.iterrows():
    for day in forecast_dates:
        rows.append({
            'sale_date': day,
            'product_id': prod['product_id'],
            'product_name': '',  # Not needed for prediction
            'category': prod['category'],
            'cost_price': prod['cost_price'],
            'unit_price': prod['selling_price'],
            'unit': prod['unit'],
            'day_of_week': day.weekday(),
            'is_weekend': int(day.weekday() in [4, 5]),
            'month': day.month,
            'day_of_month': day.day,
            'year': day.year,
            'festival': label_festival(day),
            'is_festival': int(label_festival(day) != 'none'),
            'days_to_next_festival': days_to_next_fest(day),
        })

forecast_df = pd.DataFrame(rows)
forecast_df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Generated forecast input: {OUTPUT_PATH} ({len(forecast_df)} rows)")
print(forecast_df.head(10))
