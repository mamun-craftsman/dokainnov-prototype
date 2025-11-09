import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = 'database/dokainnov.db'

# Load all product records
conn = sqlite3.connect(DB_PATH)
products_df = pd.read_sql("SELECT name, category, selling_price FROM products", conn)
conn.close()
PRODUCTS = products_df.to_dict(orient='records')

# 60 realistic Bangladeshi customers (random with repeats)
FIRST_NAMES = [
    "Abdul", "Karim", "Rahim", "Jabbar", "Mannan", "Halim", "Fatema", "Rahima", "Amina",
    "Ayesha", "Salma", "Nasrin", "Shamima", "Rashed", "Tamim", "Mushfiq", "Mahmud",
    "Jamal", "Rafiq", "Farzana", "Rozina", "Sultana", "Jannat", "Asma", "Tasnia", "Nafisa",
    "Sabbir", "Nipu", "Shakib", "Sumaiya", "Neela", "Rabeya"
]
LAST_NAMES = [
    "Mia", "Khan", "Rahman", "Ahmed", "Hossain", "Begum", "Khatun", "Akter",
    "Islam", "Ali", "Uddin", "Chowdhury", "Sarkar", "Das", "Roy", "Sheikh",
    "Siddique", "Karim"
]
customers = []
phones = set()
while len(customers) < 60:
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    phone = f"017{random.randint(10000000,99999999)}"
    if phone not in phones:
        customers.append((name, phone))
        phones.add(phone)

# Date range: 6 months plus last 8 days, ending Nov 8, 2025
end_date = datetime(2025, 11, 8)
start_date = end_date - timedelta(days=(6*30 + 8 - 1))
date_range = [start_date + timedelta(days=d) for d in range((end_date - start_date).days + 1)]

sales_rows = []
for curr_date in date_range:
    # 50–55 sales/day, but ±10% for randomness & effect
    num_sales = random.randint(45, 60)
    for _ in range(num_sales):
        cust = random.choice(customers)
        sale_date = curr_date.strftime('%Y-%m-%d')
        # 1 to 3 items per sale
        n_items = random.choices([1,2,3],[0.5,0.3,0.2])[0]
        prods = random.sample(PRODUCTS, n_items)
        discount = random.choice([0,0,0,0,5,10,20])
        paid_ratio = random.choices([1,0.7,0.4],[0.7,0.2,0.1])[0]
        cart_total = 0
        for prod in prods:
            price = float(prod['selling_price'])
            qty = random.randint(1, 6)
            subtotal = qty * price
            paid = round((subtotal - discount) * paid_ratio, 2) if discount < subtotal else subtotal*paid_ratio
            row = {
                "customer_name": cust[0],
                "customer_phone": cust[1],
                "product_name": prod['name'],
                "quantity": qty,
                "unit_price": price,
                "discount": round(discount / n_items, 2),
                "paid_amount": paid,
                "sale_date": sale_date
            }
            sales_rows.append(row)

print(f"Total records: {len(sales_rows)}")
df = pd.DataFrame(sales_rows)
df.to_csv("realistic_sales_for_forecast.csv", index=False)
print("CSV Saved: realistic_sales_for_forecast.csv")
# Optionally: Show a quick breakdown for human preview
print(df.sample(10))
