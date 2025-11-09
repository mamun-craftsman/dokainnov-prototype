import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
import math

st.set_page_config(page_title="Products", page_icon="📦", layout="wide")

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Enhanced CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    
    .page-header {
        background: linear-gradient(135deg, #00C896 0%, #0EA5E9 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .quick-add-form {
        background: #E0F7F4;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #00C896;
        margin-bottom: 1rem;
    }
    
    .table-header {
        background-color: #E0F7F4;
        padding: 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        color: #1F2937;
    }
    
    .status-ok {
        color: #10B981;
        font-weight: 600;
        background-color: #D1FAE5;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
    }
    
    .status-low {
        color: #F59E0B;
        font-weight: 600;
        background-color: #FEF3C7;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
    }
    
    .status-critical {
        color: #EF4444;
        font-weight: 600;
        background-color: #FEE2E2;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
    }
    
    .summary-panel {
        background: #F9FAFB;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
    }
    </style>
""", unsafe_allow_html=True)

# Page header
st.markdown("""
    <div class="page-header">
        <h1 style="margin:0; font-size: 2.5rem;">📦 পণ্য ব্যবস্থাপনা</h1>
        <p style="margin:0.5rem 0 0 0; opacity: 0.9;">সহজে আপনার স্টক পরিচালনা করুন</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'selected_products' not in st.session_state:
    st.session_state.selected_products = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'upload_complete' not in st.session_state:
    st.session_state.upload_complete = False

# Quick Add Form
st.markdown("### ➕ নতুন পণ্য যোগ করুন")

with st.expander("🚀 একটি পণ্য যোগ করুন (ক্লিক করুন)", expanded=st.session_state.show_add_form):
    st.markdown('<div class="quick-add-form">', unsafe_allow_html=True)
    
    form_col1, form_col2 = st.columns(2)
    
    with form_col1:
        product_name = st.text_input("পণ্যের নাম *", placeholder="যেমন: মিনিকেট চাল ৫ কেজি", key="quick_name")
        category = st.selectbox("ধরন *", 
            ["Rice", "Oil", "Flour", "Sugar", "Eggs", "Meat", "Fish", "Vegetables", 
             "Spices", "Snacks", "Beverages", "Dairy", "Bakery", "Noodles", 
             "Condiments", "Pulses", "Other"],
            key="quick_category"
        )
        cost_price = st.number_input("কেনার দাম (৳) *", min_value=0.0, step=1.0, 
                                      help="সাপ্লায়ার থেকে কত টাকায় কিনেছেন", key="quick_cost")
        selling_price = st.number_input("বিক্রয় দাম (৳) *", min_value=0.0, step=1.0,
                                         help="কাস্টমার কাছে কত টাকায় বিক্রি করবেন", key="quick_sell")
    
    with form_col2:
        current_stock = st.number_input("বর্তমান স্টক *", min_value=0, step=1, key="quick_stock")
        reorder_point = st.number_input("সতর্কতা লেভেল *", min_value=0, step=1,
                                         help="এই পরিমাণে পৌঁছালে সতর্কবার্তা দেখাবে", key="quick_reorder")
        unit = st.selectbox("একক *", ["kg", "liter", "pcs", "packet", "bottle", "dozen", "gram"], key="quick_unit")
        
        if selling_price > 0 and cost_price > 0:
            profit = selling_price - cost_price
            st.info(f"💰 লাভ প্রতি একক: ৳{profit:.2f}")
    
    if st.button("➕ পণ্য যোগ করুন", type="primary", use_container_width=True):
        if not product_name:
            st.error("পণ্যের নাম দিতে হবে!")
        elif cost_price <= 0 or selling_price <= 0:
            st.error("দাম ০ থেকে বেশি হতে হবে!")
        elif selling_price < cost_price:
            st.warning("⚠️ বিক্রয় দাম কেনার দাম থেকে কম! লোকসান হবে!")
        else:
            try:
                product_id, is_new, message = db.add_product(
                    name=product_name,
                    category=category,
                    cost_price=cost_price,
                    selling_price=selling_price,
                    current_stock=current_stock,
                    reorder_point=reorder_point,
                    unit=unit
                )
                st.success(f"✅ {message}")
                st.session_state.show_add_form = False
                st.rerun()
            except Exception as e:
                st.error(f"সমস্যা: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Bulk Upload Section
st.markdown("### 📤 অনেক পণ্য একসাথে যোগ করুন")
action_row = st.container()
with action_row:
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        # Only show uploader if not just completed
        if not st.session_state.upload_complete:
            uploaded_file = st.file_uploader(
                "CSV ফাইল আপলোড করুন",
                type=['csv'],
                help="একসাথে অনেক পণ্য যোগ করতে CSV ফাইল আপলোড করুন",
                key="csv_uploader"
            )
        else:
            st.success("✅ আপলোড সম্পন্ন হয়েছে! আরো আপলোড করতে রিফ্রেশ করুন")
            uploaded_file = None
    
    with col2:
        sample_csv = """name,category,cost_price,selling_price,current_stock,reorder_point,unit
Miniket Rice (BRRI-28) Loose,Rice,72.00,78.00,400,80,kg
Teer Soyabean Oil 1L Bottle,Oil,175.00,189.00,180,40,pcs
Pran Sugar 1kg Pack,Sugar,82.00,88.00,250,55,pcs"""
        
        st.download_button(
            label="📥 নমুনা CSV ডাউনলোড",
            data=sample_csv,
            file_name="sample_products.csv",
            mime="text/csv",
            use_container_width=True,
            help="নমুনা ফাইল ডাউনলোড করুন"
        )
    
    with col3:
        if st.button("🔄 তালিকা রিফ্রেশ", use_container_width=True):
            st.session_state.upload_complete = False
            st.rerun()

# Handle CSV upload
if uploaded_file is not None and not st.session_state.upload_complete:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Remove duplicate rows
        df = df.drop_duplicates(subset=['name'], keep='first')
        
        # Validate columns
        required_columns = ['name', 'category', 'cost_price', 'selling_price', 'current_stock', 'reorder_point', 'unit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ এই কলাম পাওয়া যায়নি: {', '.join(missing_columns)}")
            st.info("প্রয়োজনীয়: name, category, cost_price, selling_price, current_stock, reorder_point, unit")
        else:
            # Show progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            updated_count = 0
            error_count = 0
            total_rows = len(df)
            
            for idx, row in df.iterrows():
                try:
                    product_id, is_new, message = db.add_product(
                        name=row['name'],
                        category=row['category'],
                        cost_price=float(row['cost_price']),
                        selling_price=float(row['selling_price']),
                        current_stock=int(row['current_stock']),
                        reorder_point=int(row['reorder_point']),
                        unit=row['unit']
                    )
                    
                    if is_new:
                        success_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        st.warning(f"⚠️ সমস্যা: '{row['name']}': {str(e)}")
                
                # Update progress
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"প্রসেস চলছে: {idx + 1}/{total_rows}")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Show final results
            if success_count > 0 or updated_count > 0:
                st.success(f"✅ {success_count}টি নতুন পণ্য যোগ হয়েছে, {updated_count}টি পণ্য আপডেট হয়েছে!")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count}টি পণ্যে সমস্যা হয়েছে")
                
                # Mark upload as complete
                st.session_state.upload_complete = True
                
                # Rerun to show products
                st.rerun()
            else:
                st.error("❌ কোনো পণ্য যোগ হয়নি")
                
    except Exception as e:
        st.error(f"❌ ফাইল পড়তে সমস্যা: {str(e)}")

st.markdown("---")

# Get all products
all_products = db.get_all_products()
total_products = len(all_products)

if total_products == 0:
    st.info("📦 এখনো কোনো পণ্য নেই। উপরের ফর্ম বা CSV দিয়ে পণ্য যোগ করুন!")
    
    with st.expander("💡 শুরু করার গাইড"):
        st.markdown("""
        **উপায় ১: একটি পণ্য যোগ করুন**
        1. উপরের "একটি পণ্য যোগ করুন" ক্লিক করুন
        2. তথ্য পূরণ করুন
        3. "পণ্য যোগ করুন" বাটনে ক্লিক করুন
        
        **উপায় ২: অনেক পণ্য একসাথে**
        1. নমুনা CSV ডাউনলোড করুন
        2. Excel এ খুলে পণ্যের তথ্য দিন
        3. ফাইল আপলোড করুন
        
        **জরুরী তথ্য:**
        - **কেনার দাম**: সাপ্লায়ার থেকে কত টাকায় কিনেছেন
        - **বিক্রয় দাম**: কাস্টমার কাছে কত টাকায় বিক্রি করবেন
        - **স্টক**: এখন কতটা আছে
        - **সতর্কতা**: কত কমে গেলে সতর্কবার্তা চান
        """)
else:
    # Search and filter
    search_col, filter_col1, filter_col2 = st.columns([3, 1, 1])
    
    with search_col:
        search_query = st.text_input(
            "🔍 পণ্য খুঁজুন",
            value=st.session_state.search_query,
            placeholder="নাম বা ধরন লিখুন...",
            label_visibility="collapsed"
        )
        st.session_state.search_query = search_query
    
    with filter_col1:
        all_categories = sorted(list(set([p[2] for p in all_products])))
        selected_category = st.selectbox(
            "ধরন",
            ["সব ধরন"] + all_categories,
            label_visibility="collapsed"
        )
    
    with filter_col2:
        stock_filter = st.selectbox(
            "অবস্থা",
            ["সব অবস্থা", "✅ ভালো", "⚠️ কম স্টক", "🔴 জরুরী"],
            label_visibility="collapsed"
        )
    
    # Apply filters
    filtered_products = all_products
    
    if search_query:
        filtered_products = [
            p for p in filtered_products
            if search_query.lower() in p[1].lower()
            or search_query.lower() in p[2].lower()
        ]
    
    if selected_category != "সব ধরন":
        filtered_products = [p for p in filtered_products if p[2] == selected_category]
    
    if stock_filter == "✅ ভালো":
        filtered_products = [p for p in filtered_products if p[5] > p[6]]
    elif stock_filter == "⚠️ কম স্টক":
        filtered_products = [p for p in filtered_products if p[5] <= p[6] and p[5] > p[6] * 0.5]
    elif stock_filter == "🔴 জরুরী":
        filtered_products = [p for p in filtered_products if p[5] <= p[6] * 0.5]
    
    filtered_count = len(filtered_products)
    
    # Show stats
    st.markdown("### 📊 সংক্ষিপ্ত তথ্য")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    low_stock_count = sum(1 for p in all_products if p[5] <= p[6])
    critical_count = sum(1 for p in all_products if p[5] <= p[6] * 0.5)
    ok_count = sum(1 for p in all_products if p[5] > p[6])
    total_value = sum(p[4] * p[5] for p in all_products)
    
    col1.metric("মোট পণ্য", total_products)
    col2.metric("✅ ভালো আছে", ok_count)
    col3.metric("⚠️ কম আছে", low_stock_count)
    col4.metric("🔴 জরুরী", critical_count)
    col5.metric("স্টকের মূল্য", f"৳{total_value:,.0f}")
    
    st.markdown("---")
    
    # Pagination
    items_per_page = 20
    total_pages = math.ceil(filtered_count / items_per_page) if filtered_count > 0 else 1
    
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1
    
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, filtered_count)
    page_products = filtered_products[start_idx:end_idx]
    
    # Product table
    st.markdown("### 📋 পণ্যের তালিকা")
    
    if filtered_count == 0:
        st.warning(f"🔍 কোনো পণ্য পাওয়া যায়নি")
    else:
        st.caption(f"{start_idx + 1}-{end_idx} দেখাচ্ছে, মোট {filtered_count}টি")
        
        # Table header
        header_cols = st.columns([2, 1.2, 1, 1, 1, 1, 0.8, 1])
        header_cols[0].markdown("**পণ্যের নাম**")
        header_cols[1].markdown("**ধরন**")
        header_cols[2].markdown("**কেনা (৳)**")
        header_cols[3].markdown("**বিক্রয় (৳)**")
        header_cols[4].markdown("**স্টক**")
        header_cols[5].markdown("**সতর্কতা**")
        header_cols[6].markdown("**একক**")
        header_cols[7].markdown("**অবস্থা**")
        
        st.markdown("---")
        
        # Product rows
        for product in page_products:
            product_id = product[0]
            name = product[1]
            category = product[2]
            cost_price = product[3]
            selling_price = product[4]
            current_stock = product[5]
            reorder_point = product[6]
            unit = product[7]
            
            # Status
            if current_stock > reorder_point:
                status = "✅ ভালো"
                status_class = "status-ok"
            elif current_stock > reorder_point * 0.5:
                status = "⚠️ কম"
                status_class = "status-low"
            else:
                status = "🔴 জরুরী"
                status_class = "status-critical"
            
            row_cols = st.columns([2, 1.2, 1, 1, 1, 1, 0.8, 1])
            
            row_cols[0].markdown(f"{name}")
            row_cols[1].markdown(f"<small>{category}</small>", unsafe_allow_html=True)
            row_cols[2].markdown(f"৳{cost_price:,.0f}")
            row_cols[3].markdown(f"**৳{selling_price:,.0f}**")
            row_cols[4].markdown(f"{current_stock}")
            row_cols[5].markdown(f"{reorder_point}")
            row_cols[6].markdown(f"<small>{unit}</small>", unsafe_allow_html=True)
            row_cols[7].markdown(f'<span class="{status_class}">{status}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Pagination
        pagination_cols = st.columns([1, 1, 2, 1, 1])
        
        with pagination_cols[0]:
            if st.button("⏮️ প্রথম", disabled=(st.session_state.current_page == 1), use_container_width=True):
                st.session_state.current_page = 1
                st.rerun()
        
        with pagination_cols[1]:
            if st.button("⬅️ আগে", disabled=(st.session_state.current_page == 1), use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
        
        with pagination_cols[2]:
            st.markdown(f"<div style='text-align:center; padding:8px;'>পৃষ্ঠা {st.session_state.current_page} / {total_pages}</div>", unsafe_allow_html=True)
        
        with pagination_cols[3]:
            if st.button("পরে ➡️", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()
        
        with pagination_cols[4]:
            if st.button("শেষ ⏭️", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                st.session_state.current_page = total_pages
                st.rerun()
        
        # Summary
        st.markdown("---")
        st.markdown("### 📊 বিস্তারিত তথ্য")
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.markdown("**🔴 জরুরী স্টক**")
            critical_products = [p for p in all_products if p[5] <= p[6] * 0.5]
            if critical_products:
                for prod in critical_products[:5]:
                    st.markdown(f"• {prod[1]} - {prod[5]} {prod[7]}")
            else:
                st.success("✅ সব ঠিক আছে")
        
        with summary_col2:
            st.markdown("**💰 সবচেয়ে বেশি মূল্যের ধরন**")
            category_values = {}
            for prod in all_products:
                cat = prod[2]
                category_values[cat] = category_values.get(cat, 0) + (prod[4] * prod[5])
            
            for cat, value in sorted(category_values.items(), key=lambda x: x[1], reverse=True)[:5]:
                st.markdown(f"• {cat}: ৳{value:,.0f}")
        
        with summary_col3:
            st.markdown("**📈 সম্ভাব্য লাভ**")
            total_profit = sum((p[4] - p[3]) * p[5] for p in all_products)
            
            st.metric("মোট সম্ভাব্য লাভ", f"৳{total_profit:,.0f}")

st.markdown("---")
st.caption("💡 **পরামর্শ**: দ্রুত যোগ করতে একটি পণ্য ফর্ম ব্যবহার করুন, অনেক পণ্যের জন্য CSV আপলোড করুন")
