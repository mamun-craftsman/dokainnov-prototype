import streamlit as st
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import sqlite3

st.set_page_config(page_title="বিক্রয়", page_icon="🛒", layout="wide")

@st.cache_resource
def get_db():
    return DatabaseManager()
db = get_db()

# --- CSS
st.markdown("""
    <style>
    .page-header {background:linear-gradient(135deg,#00C896 0%,#0EA5E9 100%);
        padding:2rem;border-radius:10px;margin-bottom:2rem;color:white;text-align:center;}
    .cart-item {background:#F9FAFB;padding:1rem;border-radius:8px;margin:0.5rem 0;border-left:4px solid #00C896;}
    .total-box {background:#E0F7F4;padding:1.5rem;border-radius:10px;border:2px solid #00C896;margin:1rem 0;}
    .due-alert {background:#FEF3C7;color:#D97706;padding:1rem;border-radius:8px;
        border-left:4px solid #F59E0B;font-size:1.1rem;font-weight:600;margin:0.5rem 0;}
    .customer-history {background:#F0FDF4;border:2px solid #00C896;border-radius:10px;
        padding:1.5rem;margin:1rem 0;}
    </style>
""", unsafe_allow_html=True)

def safe_key(name):
    return name.replace(' ', '_').replace('.', '_').replace('-', '_').strip()

if 'cart' not in st.session_state: st.session_state.cart = []
if 'customer_name' not in st.session_state: st.session_state.customer_name = ""
if 'customer_phone' not in st.session_state: st.session_state.customer_phone = ""

st.markdown("""
    <div class="page-header">
        <h1 style="margin:0;font-size:2.5rem;">🛒 বিক্রয় কাউন্টার</h1>
        <p style="margin:0.5rem 0 0 0;opacity:0.9;">দ্রুত বিক্রয় এবং বাকি পরিশোধ</p>
    </div>
""", unsafe_allow_html=True)

today = datetime.now().date()
first_day_of_month = today.replace(day=1)

with st.spinner("পরিসংখ্যান লোড হচ্ছে..."):
    recent_sales = db.get_recent_sales_summary(limit=20000)

today_sales = [s for s in recent_sales if s[2] == str(today)]
today_revenue = sum(s[3] for s in today_sales)
today_count = len(today_sales)
due_sales = [s for s in recent_sales if s[4] == "Due"]
total_due = sum(s[6] for s in due_sales)

col1, col2, col3, col4 = st.columns(4)
col1.metric("আজকের বিক্রয়", today_count)
col2.metric("আজকের আয়", f"৳{today_revenue:,.0f}")
col3.metric("মোট বাকি", f"৳{total_due:,.0f}", delta=f"{len(set(s[1] for s in due_sales))} জন")
col4.metric("কার্টে", len(st.session_state.cart))
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🛒 নতুন বিক্রয়", "💰 বাকি পরিশোধ", "📋 সাম্প্রতিক বিক্রয়"])

# ==== TAB 1 - NEW SALES ====
with tab1:
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown("### 👤 কাস্টমার তথ্য")
        cust_col1, cust_col2 = st.columns(2)
        with cust_col1:
            customer_name = st.text_input("নাম *", value=st.session_state.customer_name, placeholder="কাস্টমারের নাম", key="cust_name")
            if len(customer_name) >= 2:
                suggestions = db.get_customer_suggestions(customer_name)
                if suggestions:
                    st.caption("📋 আগের কাস্টমার:")
                    for idx, sugg in enumerate(suggestions[:3]):
                        btn_text = f"👤 {sugg[0]}"
                        if sugg[1]: btn_text += f" • {sugg[1]}"
                        if st.button(btn_text, key=f"name_sugg_{idx}", use_container_width=True):
                            st.session_state.customer_name = sugg[0]
                            st.session_state.customer_phone = sugg[1] or ""
                            st.rerun()
        with cust_col2:
            customer_phone = st.text_input("ফোন নম্বর", value=st.session_state.customer_phone, placeholder="01712345678", max_chars=11, key="cust_phone")
            if len(customer_phone) >= 4:
                customer_data = db.search_customer_by_phone(customer_phone)
                if customer_data:
                    cust_name, cust_phone, total_purch, purch_count = customer_data
                    st.caption("📱 কাস্টমার পাওয়া গেছে:")
                    if st.button(f"👤 {cust_name} • {purch_count} বার কিনেছেন", key="phone_sugg", use_container_width=True):
                        st.session_state.customer_name = cust_name
                        st.session_state.customer_phone = cust_phone or ""
                        st.rerun()
        st.markdown("---")
        st.markdown("### 🔍 পণ্য যোগ করুন")
        search_query = st.text_input("পণ্য খুঁজুন", placeholder="পণ্যের নাম লিখুন...", key="prod_search", label_visibility="collapsed")
        if len(search_query) >= 2:
            with st.spinner("পণ্য খোঁজা হচ্ছে..."):
                products = db.search_products_with_lru(search_query, limit=10)
            if products:
                for prod in products:
                    product_id, name, price, stock, unit, last_sold = prod
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        stock_status = "✅" if stock > 20 else "⚠️" if stock > 0 else "❌"
                        st.markdown(f"{stock_status} **{name}**")
                        st.caption(f"৳{price:,.0f}/{unit} • স্টক: {stock} {unit}")
                    with col2:
                        qty = st.number_input("qty", min_value=1, max_value=max(1, stock), value=1, key=f"qty_{product_id}", label_visibility="collapsed")
                    with col3:
                        if st.button("➕", key=f"add_{product_id}", use_container_width=True):
                            if stock >= qty:
                                st.session_state.cart.append({'product_id': product_id, 'product_name': name, 'quantity': qty, 'unit_price': price, 'subtotal': price*qty, 'unit': unit})
                                st.success(f"✅ {qty} {unit} {name}")
                                st.rerun()
            else:
                st.info("🔍 পণ্য পাওয়া যায়নি")
    with col_right:
        st.markdown("### 🛒 বিক্রয় বিবরণ")
        if len(st.session_state.cart) == 0:
            st.info("📦 কার্ট খালি। পণ্য যোগ করুন।")
        else:
            for idx, item in enumerate(st.session_state.cart):
                col_item, col_remove = st.columns([5, 1])
                with col_item:
                    st.markdown(f"""<div class="cart-item"><strong>{item['product_name']}</strong><br><small>{item['quantity']} {item['unit']} × ৳{item['unit_price']:,.0f} = ৳{item['subtotal']:,.0f}</small></div>""", unsafe_allow_html=True)
                with col_remove:
                    if st.button("🗑️", key=f"rm_{idx}"):
                        st.session_state.cart.pop(idx)
                        st.rerun()
            st.markdown("---")
            st.markdown('<div class="total-box">', unsafe_allow_html=True)
            total_amount = sum(item['subtotal'] for item in st.session_state.cart)
            st.markdown(f"### মোট বিল: ৳{total_amount:,.0f}")
            discount = st.number_input("ছাড় (৳)", min_value=0.0, max_value=float(total_amount), value=0.0, step=10.0, key="disc")
            final_amount = total_amount - discount
            if discount > 0: st.markdown(f"**ছাড়ের পর:** ৳{final_amount:,.0f}")
            paid_amount = st.number_input("পরিশোধ (৳)", min_value=0.0, value=float(final_amount), step=50.0, key="paid")
            due_amount = max(0, final_amount - paid_amount)
            change_amount = max(0, paid_amount - final_amount)
            st.markdown("---")
            st.markdown(f"### সর্বমোট: ৳{final_amount:,.0f}")
            if due_amount > 0: st.markdown(f'<div class="due-alert">⚠️ বাকি: ৳{due_amount:,.0f}</div>', unsafe_allow_html=True)
            elif change_amount > 0: st.success(f"✅ ফেরত দিন: ৳{change_amount:,.0f}")
            else: st.success("✅ সম্পূর্ণ পরিশোধিত")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("💾 বিক্রয় সম্পন্ন", type="primary", use_container_width=True):
                    if not customer_name or not customer_name.strip():
                        st.error("❌ কাস্টমারের নাম দিন!")
                    else:
                        try:
                            sale_id = db.add_complete_sale(
                                customer_name=customer_name,
                                customer_phone=customer_phone,
                                cart_items=st.session_state.cart,
                                discount=discount,
                                paid_amount=paid_amount,
                                sale_date=str(today)
                            )
                            st.success(f"✅ বিক্রয় #{sale_id} সফল!")
                            st.balloons()
                            st.session_state.cart = []
                            st.session_state.customer_name = ""
                            st.session_state.customer_phone = ""
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
            with col_clear:
                if st.button("🗑️ কার্ট খালি", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()

# ==== TAB 2 - DUE PAYMENT, PAGINATION, SEE MORE, FIXED KEY ====
with tab2:
    st.markdown("### 💰 বাকি পরিশোধ করুন")
    search_term = st.text_input("🔍 নাম বা ফোন দিয়ে খুঁজুন", placeholder="নাম বা ফোন নম্বর...", key="search_due")
    with st.spinner("বাকি ডেটা লোড হচ্ছে..."):
        conn = sqlite3.connect('database/dokainnov.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.customer_name, max(c.customer_phone), SUM(s.due_amount) as total_due, COUNT(DISTINCT s.sale_id) as sale_count
            FROM sales s
            LEFT JOIN customers c ON LOWER(s.customer_name) = LOWER(c.customer_name)
            WHERE s.payment_status = 'Due'
            GROUP BY LOWER(s.customer_name)
            HAVING total_due > 0
            ORDER BY total_due DESC
        ''')
        customers_with_due = cursor.fetchall()
        conn.close()
    if search_term:
        customers_with_due = [
            c for c in customers_with_due
            if search_term.strip().lower() in c[0].lower() or (c[1] and search_term.strip() in str(c[1]))
        ]
    due_per_page = st.number_input("প্রতি পৃষ্ঠা", min_value=5, max_value=50, step=5, value=10)
    total_due_pages = (len(customers_with_due) + due_per_page - 1) // due_per_page
    due_page = st.number_input("Due পৃষ্ঠা:", min_value=1, max_value=max(1, total_due_pages), value=1)
    paged_customers = customers_with_due[(due_page-1)*due_per_page : due_page*due_per_page]
    st.caption(f"মোট {len(customers_with_due)} জন, পৃষ্ঠা {due_page}/{total_due_pages}")
    if not paged_customers:
        st.info("📭 কোনো বাকি পাওয়া যায়নি")
    for cust_name, cust_phone, total_due, sale_count in paged_customers:
        with st.container():
            st.markdown('<div class="customer-history">', unsafe_allow_html=True)
            st.markdown(f"### 👤 {cust_name}")
            if cust_phone:
                st.caption(f"📱 {cust_phone}")
            col1, col2 = st.columns(2)
            col1.metric("মোট বাকি", f"৳{total_due:,.0f}")
            col2.metric("বাকির সংখ্যা", f"{sale_count}টি বিক্রয়")
            st.markdown("---")
            due_history = db.get_customer_due_history(cust_name)
            # Pagination for individual customer's dues with a safe key
            IND_PERPAGE = 7
            history_pages = max(1, (len(due_history) + IND_PERPAGE - 1) // IND_PERPAGE)
            this_key = f"due_page_{safe_key(cust_name)}"
            page_val = st.session_state.get(this_key, 1)
            hist_page = st.number_input(
                f"{cust_name} - Due Sales Page", key=this_key,
                min_value=1, max_value=history_pages, value=page_val
            )
            show_dues = due_history[(hist_page-1)*IND_PERPAGE : hist_page*IND_PERPAGE]
            for sale_id, sale_date, final_amt, paid_amt, due_amt in show_dues:
                try:
                    date_obj = datetime.strptime(sale_date, "%Y-%m-%d")
                    date_str = date_obj.strftime("%d/%m/%Y")
                except:
                    date_str = sale_date
                with st.expander(f"📅 {date_str} • বিক্রয় #{sale_id} • বাকি ৳{due_amt:,.0f}"):
                    cols = st.columns(3)
                    cols[0].metric("মোট বিল", f"৳{final_amt:,.0f}")
                    cols[1].metric("পরিশোধিত", f"৳{paid_amt:,.0f}")
                    cols[2].metric("বাকি", f"৳{due_amt:,.0f}")
                    pay_amt = st.number_input("পরিশোধের পরিমাণ (৳)", min_value=0.0, max_value=float(due_amt), value=float(due_amt), step=50.0, key=f"pay_amt_{sale_id}")
                    if st.button("✅ পরিশোধ করুন", key=f"pay_{sale_id}", type="primary", use_container_width=True):
                        if pay_amt <= 0:
                            st.error("❌ পরিমাণ ০ এর বেশি দিতে হবে")
                        else:
                            success, new_due, msg = db.update_sale_payment(sale_id, pay_amt)
                            if success:
                                st.success(f"✅ {msg}")
                                st.balloons()
                                st.experimental_rerun()
                            else:
                                st.error(f"❌ {msg}")
                    items = db.get_sale_items(sale_id)
                    if items:
                        st.caption("**পণ্যের তালিকা:**")
                        for item in items:
                            st.caption(f"• {item[0]} × {item[1]} = ৳{item[3]:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

# ==== TAB 3 - RECENT SALES ====
with tab3:
    st.markdown("### 📋 সাম্প্রতিক বিক্রয়")
    # Filter only this month's sales
    month_sales = [s for s in recent_sales if first_day_of_month <= datetime.strptime(s[2], "%Y-%m-%d").date() <= today]

    sales_per_page = st.number_input("প্রতি পৃষ্ঠা", min_value=10, max_value=200, step=10, value=50)
    total_pages = (len(month_sales) + sales_per_page - 1) // sales_per_page
    page_selected = st.number_input("পৃষ্ঠা নির্বাচন", min_value=1, max_value=max(1, total_pages), value=1)

    # Filter by customer if requested
    search_cust = st.text_input("কাস্টমার খুঁজুন", placeholder="নাম...", key="search_cust_sales")

    # Apply name filter BEFORE slicing to page, to ensure user can find any customer across all pages.
    filtered_sales = month_sales
    if search_cust:
        filtered_sales = [s for s in filtered_sales if search_cust.strip().lower() in s[1].lower()]
    paged_sales = filtered_sales[(page_selected-1)*sales_per_page : page_selected*sales_per_page]

    st.markdown("---")

    if len(filtered_sales) == 0:
        st.info("📭 এই মাসে কোনো বিক্রয় নেই")
    else:
        st.caption(f"মোট {len(filtered_sales)} টি বিক্রয়, পৃষ্ঠা {page_selected}/{max(1, (len(filtered_sales)+sales_per_page-1)//sales_per_page)}")

        header_cols = st.columns([1,2,1.5,1.5,1.5,1])
        header_cols[0].markdown("**ID**")
        header_cols[1].markdown("**কাস্টমার**")
        header_cols[2].markdown("**তারিখ**")
        header_cols[3].markdown("**মোট**")
        header_cols[4].markdown("**পরিশোধ**")
        header_cols[5].markdown("**স্ট্যাটাস**")
        st.markdown("---")

        for sale in paged_sales:
            sale_id, cust_name, sale_date, final_amt, status, paid_amt, due_amt = sale
            try:
                date_obj = datetime.strptime(sale_date, "%Y-%m-%d")
                date_str = date_obj.strftime("%d/%m/%Y")
            except:
                date_str = sale_date
            row_cols = st.columns([1,2,1.5,1.5,1.5,1])
            row_cols[0].markdown(f"#{sale_id}")
            row_cols[1].markdown(f"{cust_name}")
            row_cols[2].markdown(f"<small>{date_str}</small>", unsafe_allow_html=True)
            row_cols[3].markdown(f"৳{final_amt:,.0f}")
            row_cols[4].markdown(f"৳{paid_amt:,.0f}")
            row_cols[5].markdown("✅" if status=="Paid" else f"৳{due_amt:,.0f}")

            with st.expander(f"বিস্তারিত #{sale_id}"):
                items = db.get_sale_items(sale_id)
                for item in items:
                    st.caption(f"• {item[0]} × {item[1]} = ৳{item[3]:,.0f}")

