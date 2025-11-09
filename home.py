import streamlit as st
from database.db_manager import DatabaseManager

# Page config
st.set_page_config(
    page_title="DokaInnov - AI Business Assistant",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_db():
    return DatabaseManager()

db = init_db()

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #00C896;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #E0F7F4;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🏪 DokaInnov</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Business Assistant for Bangladesh SMEs</p>', unsafe_allow_html=True)

# Welcome message
st.success("✅ Welcome! Navigate using the sidebar to access different features.")

# Feature overview
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Sales Forecasting")
    st.write("Predict future sales using AI models trained on Bangladesh-specific patterns (Eid, Puja seasons)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 👥 Customer Segmentation")
    st.write("Identify loyal, at-risk, and new customers for targeted offers")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 💰 Cash Flow Prediction")
    st.write("Avoid shortages with 14-day cash flow forecasts and alerts")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 📦 Smart Inventory")
    st.write("Automatic reorder alerts based on sales trends")
    st.markdown('</div>', unsafe_allow_html=True)

# Quick stats
st.markdown("---")
st.subheader("📈 Quick Overview")

# Get database stats
products_count = len(db.get_all_products())
sales_count = len(db.get_all_sales())

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Total Products", products_count)
metric_col2.metric("Total Sales", sales_count)
metric_col3.metric("System Status", "🟢 Active")

# Instructions
st.markdown("---")
st.info("""
**🚀 Getting Started:**
1. Add products in the **📦 Products** page
2. Record sales in the **🛒 Sales** page
3. View forecasts in the **📊 Forecast** page
4. Monitor cash flow in the **💰 Cash Flow** page
5. Analyze customers in the **👥 Customers** page
""")
