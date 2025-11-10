import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "database/dokainnov.db"
EXPORT_PATH = "../dokainnov_ml_engine/data/train_sales.csv"

# === Ensure output folder exists ===
os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)

# === Major festival/event windows (convert to .date() for comparison) ===
eid_al_fitr_2025 = datetime(2025, 3, 30).date()
eid_al_adha_2025 = datetime(2025, 6, 7).date()
durga_puja_start_2025 = datetime(2025, 10, 2).date()
durga_puja_end_2025   = datetime(2025, 10, 6).date()
pohela_boishakh_2025  = datetime(2025, 4, 14).date()

def label_festival(day):
    """Receives datetime.date, returns festival label string"""
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
    """Calculates days until next festival"""
    fest_days = [
        (eid_al_fitr_2025 - day).days,
        (eid_al_adha_2025 - day).days,
        (durga_puja_start_2025 - day).days,
        (pohela_boishakh_2025 - day).days,
    ]
    fest_days = [d for d in fest_days if d >= 0]
    return min(fest_days) if fest_days else -1

# === Load sales data with all relevant product info ===
conn = sqlite3.connect(DB_PATH)
query = """
SELECT
    si.sale_date,
    si.product_id,
    si.product_name,
    p.category,
    si.quantity,
    si.cost_price,
    si.unit_price,
    si.profit,
    si.subtotal,
    p.unit
FROM sale_items si
JOIN products p ON si.product_id = p.product_id
"""
df = pd.read_sql_query(query, conn)
conn.close()

# === Feature engineering ===
df["sale_date"] = pd.to_datetime(df["sale_date"])
df['day_of_week']      = df['sale_date'].dt.dayofweek
df['is_weekend']       = df['day_of_week'].isin([4, 5]).astype(int)
df['month']            = df['sale_date'].dt.month
df['day_of_month']     = df['sale_date'].dt.day
df['year']             = df['sale_date'].dt.year

# Apply festival enrichment (use .dt.date to get date objects)
df['festival'] = df['sale_date'].dt.date.apply(label_festival)
df['is_festival'] = df['festival'].apply(lambda s: int(s != 'none'))
df['days_to_next_festival'] = df['sale_date'].dt.date.apply(days_to_next_fest)

# === Export for ML ===
df.to_csv(EXPORT_PATH, index=False)
print(f"✅ Exported {len(df)} sales rows for ML to: {EXPORT_PATH}")
print("\nSample rows:")
print(df.sample(min(5, len(df))).to_string(index=False))
