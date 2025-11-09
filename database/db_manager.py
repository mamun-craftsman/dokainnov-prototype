import sqlite3
import pandas as pd
from datetime import datetime
import os
import shutil


class DatabaseManager:
    def __init__(self, db_path="database/dokainnov.db"):
        """Initialize database connection"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_database(self):
        """Create all tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT NOT NULL,
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                selling_price REAL NOT NULL CHECK(selling_price >= 0),
                current_stock INTEGER NOT NULL CHECK(current_stock >= 0),
                reorder_point INTEGER NOT NULL CHECK(reorder_point >= 0),
                unit TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sales table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                sale_date DATE NOT NULL,
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                discount REAL DEFAULT 0 CHECK(discount >= 0),
                final_amount REAL NOT NULL CHECK(final_amount >= 0),
                paid_amount REAL NOT NULL CHECK(paid_amount >= 0),
                due_amount REAL DEFAULT 0 CHECK(due_amount >= 0),
                payment_status TEXT NOT NULL CHECK(payment_status IN ('Paid', 'Due')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sale items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                profit REAL NOT NULL,
                subtotal REAL NOT NULL CHECK(subtotal >= 0),
                sale_date DATE NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
            )
        ''')
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                customer_phone TEXT,
                total_purchases REAL DEFAULT 0 CHECK(total_purchases >= 0),
                purchase_count INTEGER DEFAULT 0 CHECK(purchase_count >= 0),
                last_purchase_date DATE,
                segment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name COLLATE NOCASE)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_date ON sale_items(sale_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(customer_name COLLATE NOCASE)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(customer_phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    # ==================== PRODUCT METHODS ====================
    
    def add_product(self, name, category, cost_price, selling_price, current_stock, reorder_point, unit):
        """Add new product or update if exists (restocking)"""
        if not name or not name.strip():
            raise ValueError("Product name cannot be empty")
        
        name = name.strip()
        category = category.strip() if category else "Uncategorized"
        unit = unit.strip() if unit else "unit"
        
        cost_price = float(cost_price)
        selling_price = float(selling_price)
        current_stock = int(current_stock)
        reorder_point = int(reorder_point)
        
        if cost_price < 0 or selling_price < 0:
            raise ValueError("Prices cannot be negative")
        
        if current_stock < 0 or reorder_point < 0:
            raise ValueError("Stock values cannot be negative")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT product_id, current_stock FROM products WHERE LOWER(name) = LOWER(?)', (name,))
            existing = cursor.fetchone()
            
            if existing:
                product_id, old_stock = existing
                new_stock = old_stock + current_stock
                
                cursor.execute('''
                    UPDATE products 
                    SET current_stock = ?, cost_price = ?, selling_price = ?, 
                        reorder_point = ?, category = ?, unit = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                ''', (new_stock, cost_price, selling_price, reorder_point, category, unit, product_id))
                
                conn.commit()
                conn.close()
                return (product_id, False, f"Restocked: {old_stock} + {current_stock} = {new_stock} {unit}")
            else:
                cursor.execute('''
                    INSERT INTO products (name, category, cost_price, selling_price, current_stock, reorder_point, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, category, cost_price, selling_price, current_stock, reorder_point, unit))
                
                conn.commit()
                product_id = cursor.lastrowid
                conn.close()
                return (product_id, True, f"New product added: {name}")
                
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    def get_all_products(self):
        """Get all products ordered by most recently updated"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_id, name, category, cost_price, selling_price, current_stock, 
                   reorder_point, unit, created_at
            FROM products 
            ORDER BY updated_at DESC, product_id DESC
        ''')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product_by_id(self, product_id):
        """Get single product by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def get_product_by_name(self, name):
        """Get product by name (case-insensitive)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE LOWER(name) = LOWER(?)', (name.strip(),))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def delete_product(self, product_id):
        """Delete product (used for testing/cleanup)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()
    
    def search_products_with_lru(self, search_term, limit=10):
        """Search products with LRU sorting (most recently sold first)"""
        if not search_term or len(search_term) < 1:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT p.product_id, p.name, p.selling_price, p.current_stock, p.unit,
                   COALESCE(MAX(si.sale_date), '2000-01-01') as last_sold
            FROM products p
            LEFT JOIN sale_items si ON p.product_id = si.product_id
            WHERE LOWER(p.name) LIKE LOWER(?) AND p.current_stock > 0
            GROUP BY p.product_id
            ORDER BY last_sold DESC, p.name ASC
            LIMIT ?
        ''', (f'%{search_term}%', limit))
        
        products = cursor.fetchall()
        conn.close()
        return products
    
    # ==================== SALES METHODS ====================
    
    def add_complete_sale(self, customer_name, customer_phone, cart_items, discount, paid_amount, sale_date):
        """Add a complete sale transaction with all items"""
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required")
        
        if not cart_items or len(cart_items) == 0:
            raise ValueError("Cart cannot be empty")
        
        customer_name = customer_name.strip()
        customer_phone = customer_phone.strip() if customer_phone else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate totals
            total_amount = sum(item['subtotal'] for item in cart_items)
            
            if discount < 0 or discount > total_amount:
                raise ValueError(f"Invalid discount: {discount}")
            
            final_amount = total_amount - discount
            
            if paid_amount < 0:
                raise ValueError(f"Invalid paid amount: {paid_amount}")
            
            due_amount = max(0, final_amount - paid_amount)
            payment_status = "Paid" if due_amount <= 0 else "Due"
            
            # Insert main sale record
            cursor.execute('''
                INSERT INTO sales (customer_name, customer_phone, sale_date, total_amount, 
                                 discount, final_amount, paid_amount, due_amount, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_phone, sale_date, total_amount, discount, 
                  final_amount, paid_amount, due_amount, payment_status))
            
            sale_id = cursor.lastrowid
            
            # Insert sale items and update stock
            for item in cart_items:
                cursor.execute('SELECT current_stock, cost_price FROM products WHERE product_id = ?', (item['product_id'],))
                product_data = cursor.fetchone()
                
                if not product_data:
                    raise ValueError(f"Product ID {item['product_id']} not found")
                
                current_stock, cost_price = product_data
                
                if current_stock < item['quantity']:
                    raise ValueError(f"Insufficient stock for {item['product_name']}: need {item['quantity']}, have {current_stock}")
                
                # Calculate profit
                profit_per_unit = item['unit_price'] - cost_price
                total_profit = profit_per_unit * item['quantity']
                
                # Insert sale item
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, product_name, quantity, 
                                           unit_price, cost_price, profit, subtotal, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['product_name'], item['quantity'],
                      item['unit_price'], cost_price, total_profit, item['subtotal'], sale_date))
                
                # Update product stock
                cursor.execute('''
                    UPDATE products 
                    SET current_stock = current_stock - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                ''', (item['quantity'], item['product_id']))
            
            # Update or create customer record
            cursor.execute('SELECT customer_id FROM customers WHERE LOWER(customer_name) = LOWER(?)', (customer_name,))
            existing_customer = cursor.fetchone()
            
            if existing_customer:
                cursor.execute('''
                    UPDATE customers 
                    SET customer_phone = ?, total_purchases = total_purchases + ?,
                        purchase_count = purchase_count + 1, last_purchase_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (customer_phone, final_amount, sale_date, existing_customer[0]))
            else:
                cursor.execute('''
                    INSERT INTO customers (customer_name, customer_phone, total_purchases, 
                                          purchase_count, last_purchase_date)
                    VALUES (?, ?, ?, 1, ?)
                ''', (customer_name, customer_phone, final_amount, sale_date))
            
            conn.commit()
            return sale_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def add_bulk_sale_from_csv(self, customer_name, customer_phone, product_name, quantity, unit_price, discount, paid_amount, sale_date):
        """Add a sale from CSV data (for bulk import - doesn't reduce stock)"""
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required")
        
        customer_name = customer_name.strip()
        customer_phone = customer_phone.strip() if customer_phone else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Find product by name
            cursor.execute('SELECT product_id, cost_price FROM products WHERE LOWER(name) = LOWER(?)', (product_name.strip(),))
            product_data = cursor.fetchone()
            
            if not product_data:
                conn.close()
                return (False, f"Product not found: {product_name}")
            
            product_id, cost_price = product_data
            
            # Calculate amounts
            subtotal = quantity * unit_price
            final_amount = subtotal - discount
            due_amount = max(0, final_amount - paid_amount)
            payment_status = "Paid" if due_amount <= 0 else "Due"
            
            # Insert sale record
            cursor.execute('''
                INSERT INTO sales (customer_name, customer_phone, sale_date, total_amount, 
                                 discount, final_amount, paid_amount, due_amount, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_phone, sale_date, subtotal, discount, 
                  final_amount, paid_amount, due_amount, payment_status))
            
            sale_id = cursor.lastrowid
            
            # Calculate profit
            profit = (unit_price - cost_price) * quantity
            
            # Insert sale item (DON'T update stock for historical data)
            cursor.execute('''
                INSERT INTO sale_items (sale_id, product_id, product_name, quantity, 
                                       unit_price, cost_price, profit, subtotal, sale_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sale_id, product_id, product_name, quantity, unit_price, cost_price, profit, subtotal, sale_date))
            
            # Update or create customer
            cursor.execute('SELECT customer_id FROM customers WHERE LOWER(customer_name) = LOWER(?)', (customer_name,))
            existing_customer = cursor.fetchone()
            
            if existing_customer:
                cursor.execute('''
                    UPDATE customers 
                    SET customer_phone = ?, total_purchases = total_purchases + ?,
                        purchase_count = purchase_count + 1, last_purchase_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (customer_phone, final_amount, sale_date, existing_customer[0]))
            else:
                cursor.execute('''
                    INSERT INTO customers (customer_name, customer_phone, total_purchases, 
                                          purchase_count, last_purchase_date)
                    VALUES (?, ?, ?, 1, ?)
                ''', (customer_name, customer_phone, final_amount, sale_date))
            
            conn.commit()
            conn.close()
            return (True, f"Sale added: {product_name}")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return (False, f"Error: {str(e)}")
    
    def get_recent_sales_summary(self, limit=1000):
        """Get recent sales summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sale_id, customer_name, sale_date, final_amount, payment_status, 
                   paid_amount, due_amount
            FROM sales
            ORDER BY sale_date DESC, created_at DESC
            LIMIT ?
        ''', (limit,))
        sales = cursor.fetchall()
        conn.close()
        return sales
    
    def get_sale_items(self, sale_id):
        """Get items for a specific sale"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_name, quantity, unit_price, subtotal
            FROM sale_items
            WHERE sale_id = ?
        ''', (sale_id,))
        items = cursor.fetchall()
        conn.close()
        return items
    
    def update_sale_payment(self, sale_id, additional_payment):
        """Update payment for a sale (for paying off dues)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT final_amount, paid_amount, due_amount 
                FROM sales 
                WHERE sale_id = ?
            ''', (sale_id,))
            
            sale_data = cursor.fetchone()
            if not sale_data:
                conn.close()
                return (False, 0, "Sale not found")
            
            final_amount, current_paid, current_due = sale_data
            
            new_paid = current_paid + additional_payment
            new_due = max(0, final_amount - new_paid)
            new_status = "Paid" if new_due <= 0 else "Due"
            
            cursor.execute('''
                UPDATE sales 
                SET paid_amount = ?, due_amount = ?, payment_status = ?
                WHERE sale_id = ?
            ''', (new_paid, new_due, new_status, sale_id))
            
            conn.commit()
            conn.close()
            
            return (True, new_due, f"Payment updated. Remaining: ৳{new_due:,.0f}")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return (False, 0, f"Error: {str(e)}")
    
    # ==================== CUSTOMER METHODS ====================
    
    def get_customer_suggestions(self, search_term):
        """Get customer suggestions for autocomplete (by name)"""
        if not search_term or len(search_term) < 2:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT customer_name, customer_phone, last_purchase_date
            FROM customers
            WHERE LOWER(customer_name) LIKE LOWER(?)
            ORDER BY last_purchase_date DESC
            LIMIT 5
        ''', (f'%{search_term}%',))
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def search_customer_by_phone(self, phone):
        """Search customer by phone number"""
        if not phone or len(phone) < 4:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT customer_name, customer_phone, total_purchases, purchase_count
            FROM customers
            WHERE customer_phone LIKE ?
            ORDER BY last_purchase_date DESC
            LIMIT 1
        ''', (f'%{phone}%',))
        customer = cursor.fetchone()
        conn.close()
        return customer
    
    def get_customer_due_history(self, customer_name):
        """Get all due sales for a specific customer grouped by date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sale_id, sale_date, final_amount, paid_amount, due_amount
            FROM sales
            WHERE LOWER(customer_name) = LOWER(?) AND payment_status = 'Due'
            ORDER BY sale_date DESC
        ''', (customer_name.strip(),))
        sales = cursor.fetchall()
        conn.close()
        return sales
    
    def get_all_customers(self):
        """Get all customers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM customers 
            ORDER BY total_purchases DESC
        ''')
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    # ==================== ML EXPORT METHODS ====================
    
    def export_sales_for_ml(self, days=180):
        """Export sales data in ML-ready format for forecasting"""
        conn = self.get_connection()
        
        query = f'''
            SELECT 
                si.sale_date,
                si.product_id,
                si.product_name,
                p.category,
                si.quantity,
                si.cost_price,
                si.unit_price as selling_price,
                si.profit,
                si.subtotal,
                p.unit,
                CAST(strftime('%w', si.sale_date) AS INTEGER) as day_of_week,
                CAST(strftime('%m', si.sale_date) AS INTEGER) as month,
                CAST(strftime('%d', si.sale_date) AS INTEGER) as day_of_month,
                CAST(strftime('%Y', si.sale_date) AS INTEGER) as year
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_date >= date('now', '-{days} days')
            ORDER BY si.sale_date ASC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_product_sales_history(self, product_id, days=180):
        """Get sales history for a specific product"""
        conn = self.get_connection()
        
        query = f'''
            SELECT sale_date, SUM(quantity) as total_quantity, 
                   SUM(profit) as total_profit, COUNT(*) as num_sales
            FROM sale_items
            WHERE product_id = ? AND sale_date >= date('now', '-{days} days')
            GROUP BY sale_date
            ORDER BY sale_date ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(product_id,))
        conn.close()
        return df
    
    # ==================== ANALYTICS METHODS ====================
    
    def get_database_stats(self):
        """Get overall database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM products')
        stats['total_products'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sales')
        stats['total_sales'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customers')
        stats['total_customers'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(final_amount), 0) FROM sales')
        stats['total_revenue'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(profit), 0) FROM sale_items')
        stats['total_profit'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*), COALESCE(SUM(final_amount), 0) FROM sales WHERE sale_date = date("now")')
        today_data = cursor.fetchone()
        stats['today_sales_count'] = today_data[0]
        stats['today_revenue'] = today_data[1]
        
        cursor.execute('SELECT COALESCE(SUM(profit), 0) FROM sale_items WHERE sale_date = date("now")')
        stats['today_profit'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(due_amount), 0) FROM sales WHERE payment_status = "Due"')
        stats['total_due'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_top_selling_products(self, limit=10, days=30):
        """Get top selling products with profit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT 
                si.product_name,
                SUM(si.quantity) as total_quantity,
                COUNT(DISTINCT si.sale_id) as num_sales,
                SUM(si.subtotal) as total_revenue,
                SUM(si.profit) as total_profit
            FROM sale_items si
            WHERE si.sale_date >= date('now', '-{days} days')
            GROUP BY si.product_id
            ORDER BY total_quantity DESC
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_low_stock_products(self):
        """Get products below reorder point"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_id, name, current_stock, reorder_point, cost_price, 
                   selling_price, (selling_price - cost_price) as profit_margin, 
                   category, unit
            FROM products
            WHERE current_stock <= reorder_point
            ORDER BY (current_stock * 1.0 / NULLIF(reorder_point, 0)) ASC
        ''')
        products = cursor.fetchall()
        conn.close()
        return products
    
    # ==================== UTILITY METHODS ====================
    
    def clear_all_data(self):
        """Clear all data from database (useful for testing)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sale_items')
        cursor.execute('DELETE FROM sales')
        cursor.execute('DELETE FROM customers')
        cursor.execute('DELETE FROM products')
        cursor.execute('DELETE FROM sqlite_sequence')
        
        conn.commit()
        conn.close()
        print("⚠️ All data cleared from database")
    
    def backup_database(self, backup_path=None):
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"database/backup_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
