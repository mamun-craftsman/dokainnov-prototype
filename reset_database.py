from database.db_manager import DatabaseManager

print("🗑️ Deleting all products...")

db = DatabaseManager()

# Get count before deletion
products = db.get_all_products()
count = len(products)

if count == 0:
    print("✅ No products to delete")
else:
    print(f"Found {count} products")
    
    confirm = input(f"Delete all {count} products? Type 'yes' to confirm: ")
    
    if confirm.lower() == 'yes':
        import sqlite3
        conn = sqlite3.connect('database/dokainnov.db')
        cursor = conn.cursor()
        
        # Delete all products
        cursor.execute('DELETE FROM products')
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        print(f"✅ Deleted {deleted} products!")
    else:
        print("❌ Cancelled")
