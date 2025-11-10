import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Customer Insights",
    page_icon="👥",
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.segment-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.3s;
    border: 2px solid transparent;
}
.segment-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.segment-new {
    border-color: #10b981;
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}
.segment-recent {
    border-color: #3b82f6;
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}
.segment-repeated {
    border-color: #8b5cf6;
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
}
.segment-ghost {
    border-color: #f59e0b;
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}
.segment-due {
    border-color: #ef4444;
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}
.customer-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    border-left: 4px solid #8b5cf6;
    transition: all 0.3s;
}
.customer-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    transform: translateX(5px);
}
.stat-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    margin: 0.25rem;
}
.badge-green {
    background: #d1fae5;
    color: #065f46;
}
.badge-blue {
    background: #dbeafe;
    color: #1e40af;
}
.badge-purple {
    background: #ede9fe;
    color: #5b21b6;
}
.badge-red {
    background: #fee2e2;
    color: #991b1b;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

st.markdown("""
<div class="main-header">
    <h1>👥 Customer Insights</h1>
    <p>Understand your customers better with smart segmentation</p>
</div>
""", unsafe_allow_html=True)

customers = db.get_all_customers()

new_customers = [c for c in customers if (datetime.now() - datetime.fromisoformat(c[7])).days <= 7]
recent_customers = [c for c in customers if c[5] and (datetime.now() - datetime.fromisoformat(c[5])).days <= 30]
repeated_customers = [c for c in customers if c[4] >= 5]
ghost_customers = [c for c in customers if c[5] and (datetime.now() - datetime.fromisoformat(c[5])).days > 90]

due_customers = []
try:
    import sqlite3
    conn = sqlite3.connect('database/dokainnov.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT customer_name, SUM(due_amount) as total_due
        FROM sales
        WHERE payment_status = 'Due'
        GROUP BY customer_name
        ORDER BY total_due DESC
        LIMIT 10
    """)
    due_customers = cursor.fetchall()
    conn.close()
except:
    pass

st.markdown("## 📊 Customer Segments")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown('<div class="segment-card segment-new">', unsafe_allow_html=True)
    st.markdown("🆕")
    st.markdown(f"<h2>{len(new_customers)}</h2>", unsafe_allow_html=True)
    st.markdown("**New Customers**")
    st.caption("Last 7 days")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="segment-card segment-recent">', unsafe_allow_html=True)
    st.markdown("🔥")
    st.markdown(f"<h2>{len(recent_customers)}</h2>", unsafe_allow_html=True)
    st.markdown("**Active Customers**")
    st.caption("Last 30 days")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="segment-card segment-repeated">', unsafe_allow_html=True)
    st.markdown("⭐")
    st.markdown(f"<h2>{len(repeated_customers)}</h2>", unsafe_allow_html=True)
    st.markdown("**Loyal Customers**")
    st.caption("5+ purchases")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown('<div class="segment-card segment-ghost">', unsafe_allow_html=True)
    st.markdown("👻")
    st.markdown(f"<h2>{len(ghost_customers)}</h2>", unsafe_allow_html=True)
    st.markdown("**Ghost Customers**")
    st.caption("90+ days absent")
    st.markdown("</div>", unsafe_allow_html=True)

with col5:
    st.markdown('<div class="segment-card segment-due">', unsafe_allow_html=True)
    st.markdown("💳")
    st.markdown(f"<h2>{len(due_customers)}</h2>", unsafe_allow_html=True)
    st.markdown("**Due Customers**")
    st.caption("Pending payments")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🆕 New", "⭐ Loyal", "👻 Ghost", "💳 Due", "📋 All Customers"])

with tab1:
    st.markdown("### 🆕 New Customers (Last 7 Days)")
    
    if new_customers:
        for customer in new_customers[:10]:
            st.markdown('<div class="customer-card">', unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns([3, 2, 2])
            
            with col_a:
                st.markdown(f"**👤 {customer[1]}**")
                if customer[2]:
                    st.caption(f"📞 {customer[2]}")
            
            with col_b:
                st.markdown(f'<span class="stat-badge badge-green">৳{customer[3]:,.0f} spent</span>', unsafe_allow_html=True)
            
            with col_c:
                st.markdown(f'<span class="stat-badge badge-blue">{customer[4]} purchases</span>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No new customers in the last 7 days")

with tab2:
    st.markdown("### ⭐ Loyal Customers (5+ Purchases)")
    
    if repeated_customers:
        sorted_loyal = sorted(repeated_customers, key=lambda x: x[3], reverse=True)
        
        for customer in sorted_loyal[:15]:
            st.markdown('<div class="customer-card">', unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns([3, 2, 2])
            
            with col_a:
                st.markdown(f"**👤 {customer[1]}**")
                if customer[2]:
                    st.caption(f"📞 {customer[2]}")
            
            with col_b:
                st.markdown(f'<span class="stat-badge badge-purple">৳{customer[3]:,.0f} lifetime</span>', unsafe_allow_html=True)
            
            with col_c:
                st.markdown(f'<span class="stat-badge badge-blue">{customer[4]} visits</span>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No loyal customers yet (need 5+ purchases)")

with tab3:
    st.markdown("### 👻 Ghost Customers (90+ Days Absent)")
    
    if ghost_customers:
        sorted_ghost = sorted(ghost_customers, key=lambda x: datetime.fromisoformat(x[5]), reverse=False)
        
        for customer in sorted_ghost[:15]:
            last_purchase = datetime.fromisoformat(customer[5])
            days_absent = (datetime.now() - last_purchase).days
            
            st.markdown('<div class="customer-card">', unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns([3, 2, 2])
            
            with col_a:
                st.markdown(f"**👤 {customer[1]}**")
                if customer[2]:
                    st.caption(f"📞 {customer[2]}")
            
            with col_b:
                st.markdown(f'<span class="stat-badge badge-red">{days_absent} days absent</span>', unsafe_allow_html=True)
            
            with col_c:
                st.markdown(f'<span class="stat-badge badge-purple">৳{customer[3]:,.0f} spent</span>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("No ghost customers! Everyone is active!")

with tab4:
    st.markdown("### 💳 Customers with Pending Dues")
    
    if due_customers:
        for customer_name, due_amount in due_customers:
            st.markdown('<div class="customer-card">', unsafe_allow_html=True)
            col_a, col_b = st.columns([4, 2])
            
            with col_a:
                st.markdown(f"**👤 {customer_name}**")
            
            with col_b:
                st.markdown(f'<span class="stat-badge badge-red">৳{due_amount:,.0f} due</span>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("🎉 No pending dues! All customers have paid!")

with tab5:
    st.markdown("### 📋 All Customers")
    
    search = st.text_input("🔍 Search customers", placeholder="Name or phone...")
    
    filtered = customers
    if search:
        filtered = [c for c in customers if search.lower() in c[1].lower() or (c[2] and search in c[2])]
    
    sorted_customers = sorted(filtered, key=lambda x: x[3], reverse=True)
    
    for customer in sorted_customers[:50]:
        st.markdown('<div class="customer-card">', unsafe_allow_html=True)
        col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 2])
        
        with col_a:
            st.markdown(f"**👤 {customer[1]}**")
            if customer[2]:
                st.caption(f"📞 {customer[2]}")
        
        with col_b:
            st.markdown(f'<span class="stat-badge badge-purple">৳{customer[3]:,.0f}</span>', unsafe_allow_html=True)
        
        with col_c:
            st.markdown(f'<span class="stat-badge badge-blue">{customer[4]} visits</span>', unsafe_allow_html=True)
        
        with col_d:
            if customer[5]:
                last_date = datetime.fromisoformat(customer[5]).strftime("%d %b")
                st.caption(f"Last: {last_date}")
        
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("👥 Customer Insights & Segmentation System")
