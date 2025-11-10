#!/usr/bin/env python3
import sqlite3
import shutil
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "dokainnov.db"
SCHEMA_PATH = BASE / "schema.sql"
BACKUP_PATH = BASE / f"dokainnov_backup_before_schema_{__import__('time').time():.0f}.db"

if not DB_PATH.exists():
    print(f"ERROR: DB not found at {DB_PATH}")
    sys.exit(1)

# 1) backup
shutil.copy2(DB_PATH, BACKUP_PATH)
print(f"Backup created at: {BACKUP_PATH}")

# 2) apply schema.sql using executescript
with sqlite3.connect(DB_PATH) as conn:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        conn.executescript(sql)
        print("Schema applied successfully.")
    except sqlite3.DatabaseError as e:
        print("ERROR applying schema:", e)
        print("Restoring backup...")
        shutil.copy2(BACKUP_PATH, DB_PATH)
        print("Backup restored.")
        sys.exit(1)

# 3) verify table exists and list it
with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='product_forecasts';"
    )
    row = cur.fetchone()
    if row:
        print("✅ Table product_forecasts exists.")
        # show schema for confirmation
        cur.execute("PRAGMA table_info(product_forecasts);")
        cols = cur.fetchall()
        print("Columns:")
        for c in cols:
            print(" ", c)
    else:
        print("ERROR: product_forecasts not created.")
