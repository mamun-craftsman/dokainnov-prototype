import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
from io import BytesIO
from openai import OpenAI
from gtts import gTTS

sys.path.append(str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Cashflow Management",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.asset-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.asset-card:hover {
    transform: translateY(-5px);
}
.cash-card {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.cash-card:hover {
    transform: translateY(-5px);
}
.inventory-card {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.inventory-card:hover {
    transform: translateY(-5px);
}
.due-card {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}
.due-card:hover {
    transform: translateY(-5px);
}
.transaction-in {
    background: #D1FAE5;
    border-left: 4px solid #10b981;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.transaction-out {
    background: #FEE2E2;
    border-left: 4px solid #ef4444;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.ai-advice-box {
    background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);
    padding: 2rem;
    border-radius: 15px;
    border-left: 6px solid #667eea;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

st.markdown("""
<div class="main-header">
    <h1>💰 Cashflow Management</h1>
    <p>Track your money, assets, and dues in real-time</p>
</div>
""", unsafe_allow_html=True)

try:
    cash_balance = db.get_current_cash_balance()
    inventory_value = db.get_inventory_value()
    total_dues = db.get_total_dues()
    total_assets = cash_balance + inventory_value + total_dues
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.markdown("## 📊 Total Assets Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="asset-card">', unsafe_allow_html=True)
    st.markdown(f"<h3>Total Assets</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1>৳{total_assets:,.0f}</h1>", unsafe_allow_html=True)
    st.caption("Cash + Inventory + Dues")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="cash-card">', unsafe_allow_html=True)
    st.markdown(f"<h3>💵 Cash in Hand</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1>৳{cash_balance:,.0f}</h1>", unsafe_allow_html=True)
    st.caption("Available now")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="inventory-card">', unsafe_allow_html=True)
    st.markdown(f"<h3>📦 Inventory Value</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1>৳{inventory_value:,.0f}</h1>", unsafe_allow_html=True)
    try:
        conn = sqlite3.connect('database/dokainnov.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock > 0")
        product_count = cursor.fetchone()[0]
        conn.close()
        st.caption(f"{product_count} products in stock")
    except:
        st.caption("Stock value")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown('<div class="due-card">', unsafe_allow_html=True)
    st.markdown(f"<h3>⏳ Total Dues</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1>৳{total_dues:,.0f}</h1>", unsafe_allow_html=True)
    st.caption("To collect")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 💰 Cash Flow Breakdown")

try:
    conn = sqlite3.connect('database/dokainnov.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM sales")
    total_sales_cash = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM cash_transactions WHERE transaction_type = 'OUT'")
    total_expenses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM cash_transactions WHERE transaction_type = 'IN'")
    manual_cash_in = cursor.fetchone()[0]
    
    conn.close()
except Exception as e:
    st.error(f"Error calculating breakdown: {e}")
    total_sales_cash = 0
    total_expenses = 0
    manual_cash_in = 0

col_break1, col_break2, col_break3, col_break4 = st.columns(4)

with col_break1:
    st.metric("💰 Sales Revenue", f"৳{total_sales_cash:,.0f}", help="Cash received from sales")

with col_break2:
    st.metric("➕ Other Income", f"৳{manual_cash_in:,.0f}", help="Loans, investments, etc.")

with col_break3:
    st.metric("➖ Expenses", f"৳{total_expenses:,.0f}", help="All spending", delta=f"-{total_expenses:,.0f}", delta_color="inverse")

with col_break4:
    net_formula = total_sales_cash + manual_cash_in - total_expenses
    st.metric("= Net Cash", f"৳{net_formula:,.0f}", help="Final balance")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["💵 Transactions", "➕ Add Money", "➖ Spend Money", "📋 Dues"])

with tab1:
    st.markdown("### Recent Cash Transactions")
    
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        days_filter = st.selectbox("Time Period", [7, 15, 30, 60, 90], index=2, key="days_trans")
    
    with col_filter2:
        type_filter = st.selectbox("Type", ["All", "IN", "OUT"], key="type_trans")
    
    try:
        summary = db.get_cashflow_summary(days_filter)
        
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        
        with col_sum1:
            st.metric("Money IN", f"৳{summary['total_in']:,.0f}")
        
        with col_sum2:
            st.metric("Money OUT", f"৳{summary['total_out']:,.0f}")
        
        with col_sum3:
            net_color = "normal" if summary['net'] >= 0 else "inverse"
            st.metric("Net Flow", f"৳{summary['net']:,.0f}", delta=f"{summary['net']:,.0f}", delta_color=net_color)
    except Exception as e:
        st.warning(f"Could not load summary: {e}")
    
    try:
        transactions = db.get_cash_transactions(days_filter)
        
        if transactions:
            for trans in transactions:
                trans_id, trans_type, amount, category, description, date, created = trans
                
                css_class = "transaction-in" if trans_type == "IN" else "transaction-out"
                symbol = "➕" if trans_type == "IN" else "➖"
                
                if type_filter == "All" or type_filter == trans_type:
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    col_a, col_b, col_c = st.columns([2, 4, 2])
                    col_a.markdown(f"**{symbol} ৳{amount:,.0f}**")
                    col_b.markdown(f"**{category}**<br><small>{description}</small>", unsafe_allow_html=True)
                    col_c.markdown(f"*{date}*")
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📭 No manual transactions in this period. Sales revenue is tracked automatically.")
    except Exception as e:
        st.error(f"Error loading transactions: {e}")

with tab2:
    st.markdown("### ➕ Add Money to Business")
    st.caption("Record money coming in (besides sales)")
    
    with st.form("add_money_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            amount_in = st.number_input("Amount (৳)", min_value=0.0, step=100.0, format="%.2f", key="amount_in")
            category_in = st.selectbox("Category", [
                "Investment",
                "Loan Received",
                "Grant/Subsidy",
                "Other Income"
            ], key="cat_in")
        
        with col2:
            date_in = st.date_input("Date", value=datetime.now(), key="date_in")
            description_in = st.text_area("Description", placeholder="e.g., Personal investment, Bank loan, etc.", key="desc_in")
        
        submitted_in = st.form_submit_button("💰 Add Money", use_container_width=True, type="primary")
        
        if submitted_in:
            if amount_in > 0:
                try:
                    db.add_cash_transaction(
                        transaction_type='IN',
                        amount=amount_in,
                        category=category_in,
                        description=description_in or "No description",
                        transaction_date=date_in
                    )
                    st.success(f"✅ Added ৳{amount_in:,.0f} to cash!")
                    st.balloons()
                    st.session_state.refresh_trigger += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("⚠️ Amount must be greater than 0")

with tab3:
    st.markdown("### ➖ Record Business Expense")
    st.caption("Track all money spent")
    
    if cash_balance <= 0:
        st.warning("⚠️ Cash balance is zero or negative!")
    
    with st.form("spend_money_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            amount_out = st.number_input("Amount (৳)", min_value=0.0, step=100.0, format="%.2f", key="amount_out")
            category_out = st.selectbox("Category", [
                "Product Purchase/Restock",
                "Rent",
                "Salary/Wages",
                "Utilities (Electric/Water/Gas)",
                "Transport",
                "Maintenance/Repairs",
                "Taxes/Fees",
                "Marketing/Advertising",
                "Other Expense"
            ], key="cat_out")
        
        with col2:
            date_out = st.date_input("Date", value=datetime.now(), key="date_out")
            description_out = st.text_area("Description", placeholder="e.g., Bought 50kg rice, Paid rent for shop, etc.", key="desc_out")
        
        submitted_out = st.form_submit_button("💸 Record Expense", use_container_width=True, type="primary")
        
        if submitted_out:
            if amount_out > 0:
                if amount_out > cash_balance:
                    st.warning(f"⚠️ Expense (৳{amount_out:,.0f}) exceeds cash balance (৳{cash_balance:,.0f})!")
                
                try:
                    db.add_cash_transaction(
                        transaction_type='OUT',
                        amount=amount_out,
                        category=category_out,
                        description=description_out or "No description",
                        transaction_date=date_out
                    )
                    st.success(f"✅ Recorded expense of ৳{amount_out:,.0f}")
                    st.session_state.refresh_trigger += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("⚠️ Amount must be greater than 0")

with tab4:
    st.markdown("### 📋 Customer Dues Analysis")
    
    try:
        dues = db.get_dues_breakdown()
        
        if dues:
            st.info(f"**{len(dues)} customers** owe a total of **৳{total_dues:,.0f}**")
            
            st.markdown("---")
            
            for customer_name, phone, due_amount, due_count, oldest_days in dues:
                with st.expander(f"👤 {customer_name} - ৳{due_amount:,.0f} pending"):
                    col1, col2, col3 = st.columns(3)
                    
                    col1.metric("Total Due", f"৳{due_amount:,.0f}")
                    col2.metric("Pending Sales", f"{due_count}")
                    col3.metric("Oldest Due", f"{int(oldest_days)} days ago")
                    
                    if phone:
                        st.markdown(f"📞 **Phone:** {phone}")
                    
                    if oldest_days > 60:
                        st.error(f"🚨 Urgent! Due is {int(oldest_days)} days old")
                    elif oldest_days > 30:
                        st.warning(f"⚠️ Follow up recommended - {int(oldest_days)} days old")
        else:
            st.success("🎉 No pending dues! All customers have paid in full.")
    except Exception as e:
        st.error(f"Error loading dues: {e}")

st.markdown("---")
st.markdown("## 🤖 AI Cashflow Advisor")

if st.button("🧠 Get AI Business Advice", type="primary", use_container_width=True):
    with st.spinner("AI analyzing your cashflow..."):
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key="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",
            )
            
            context = f"""আপনি একজন ব্যবসা উপদেষ্টা। বাংলাদেশের একটি ছোট দোকানের cashflow analyze করুন।

Current Status:
- Total Assets: ৳{total_assets:,.0f}
- Cash in Hand: ৳{cash_balance:,.0f}
- Inventory Value: ৳{inventory_value:,.0f}
- Total Dues: ৳{total_dues:,.0f}

Breakdown:
- Sales Revenue: ৳{total_sales_cash:,.0f}
- Other Income: ৳{manual_cash_in:,.0f}
- Total Expenses: ৳{total_expenses:,.0f}

2-3 বাক্যে সহজ বাংলায় পরামর্শ দিন:
- Cash situation কেমন?
- কোথায় সমস্যা?
- কি করা উচিত?"""
            
            response = client.chat.completions.create(
                model="tngtech/deepseek-r1t2-chimera:free",
                messages=[{"role": "user", "content": context}],
                temperature=0.7,
                max_tokens=300,
            )
            
            advice = response.choices[0].message.content.strip()
            
            st.markdown('<div class="ai-advice-box">', unsafe_allow_html=True)
            st.markdown(f"**💡 AI Business Advice:**\n\n{advice}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            try:
                tts = gTTS(text=advice, lang='bn', slow=False)
                audio_buffer = BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                st.audio(audio_buffer.read(), format="audio/mp3")
            except Exception as audio_err:
                st.caption("(Audio generation skipped)")
            
        except Exception as e:
            st.error(f"AI analysis failed: {e}")

st.markdown("---")
st.caption("💰 Cashflow Management System | Cash = Sales Revenue + Other Income - Expenses")
