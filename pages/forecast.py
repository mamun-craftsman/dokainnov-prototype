import streamlit as st
import pandas as pd
import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
from gtts import gTTS
import tempfile
import os

sys.path.append(str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager

ML_DIR = Path(__file__).parent.parent.parent / "dokainnov_ml_engine"
ML_PYTHON = str(ML_DIR / "venv" / "Scripts" / "python.exe")

st.set_page_config(
    page_title="AI Demand Forecast",
    page_icon="🔮",
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.forecast-box {
    background: #FEF3C7;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #F59E0B;
    margin-top: 1rem;
}
.metric-card {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    text-align: center;
}
.summary-box {
    background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);
    padding: 2rem;
    border-radius: 15px;
    border-left: 6px solid #667eea;
    margin: 2rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.summary-title {
    color: #4338ca;
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

if 'selected_products' not in st.session_state:
    st.session_state.selected_products = set()
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""
if 'external_context' not in st.session_state:
    st.session_state.external_context = ""
if 'forecast_results' not in st.session_state:
    st.session_state.forecast_results = None
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None
if 'show_summary' not in st.session_state:
    st.session_state.show_summary = False

def get_last_forecast(product_id):
    try:
        conn = sqlite3.connect('database/dokainnov.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT forecast_date, ai_advice, expected_profit, reorder_needed, forecast_qty
            FROM product_forecasts
            WHERE product_id = ?
            ORDER BY forecast_date DESC
            LIMIT 1
        """, (product_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        return None

def save_external_context(context_text):
    context_file = ML_DIR / "data" / "external_context.txt"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    with open(context_file, 'w', encoding='utf-8') as f:
        f.write(context_text)

def save_forecasts_to_database():
    JSON_PATH = ML_DIR / "data" / "ai_recommendations.json"
    CSV_PATH = ML_DIR / "data" / "forecast_output.csv"
    DB_PATH = Path("database/dokainnov.db")
    
    if not JSON_PATH.exists() or not CSV_PATH.exists():
        return 0
    
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            ai_data = json.load(f)
        
        forecast_df = pd.read_csv(CSV_PATH)
        
        weekly_forecast = forecast_df.groupby('product_id').agg({
            'forecast_qty': 'sum',
            'cost_price': 'first',
            'unit_price': 'first'
        }).reset_index()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_id, current_stock FROM products")
        stock_dict = dict(cursor.fetchall())
        
        inserted = 0
        
        for ai_rec in ai_data.get('products', []):
            try:
                pid = int(ai_rec['product_id'])
                advice = ai_rec.get('advice', '')
                
                forecast_row = weekly_forecast[weekly_forecast['product_id'] == pid]
                if forecast_row.empty:
                    continue
                
                qty = float(forecast_row['forecast_qty'].iloc[0])
                cost = float(forecast_row['cost_price'].iloc[0])
                price = float(forecast_row['unit_price'].iloc[0])
                
                profit_per_unit = price - cost
                expected_profit = qty * profit_per_unit
                stock = stock_dict.get(pid, 0)
                reorder = max(0, qty - stock)
                
                cursor.execute("""
                    INSERT INTO product_forecasts 
                    (product_id, forecast_date, forecast_qty, expected_profit, reorder_needed, ai_advice)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), qty, expected_profit, reorder, advice))
                
                inserted += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        return inserted
    except Exception as e:
        st.error(f"Database save error: {e}")
        return 0

def generate_bangla_audio(text):
    try:
        from io import BytesIO
        
        tts = gTTS(text=text, lang='bn', slow=False)
        
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return audio_buffer.read()
    except Exception as e:
        st.warning(f"Audio generation failed: {e}")
        return None


def run_forecast_pipeline(product_ids):
    if st.session_state.external_context:
        save_external_context(st.session_state.external_context)
    
    product_ids_str = ",".join(map(str, product_ids))
    
    with st.spinner("🔄 Step 1/3: Generating forecast input..."):
        result = subprocess.run([
            ML_PYTHON,
            str(Path(__file__).parent.parent / "generate_forecast_input.py"),
            "--products", 
            product_ids_str
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"❌ Input Error: {result.stderr}")
            return False
    
    with st.spinner("🤖 Step 2/3: Running ML predictions..."):
        result = subprocess.run([
            ML_PYTHON,
            str(ML_DIR / "forecast.py")
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"❌ ML Error: {result.stderr}")
            return False
    
    with st.spinner("🧠 Step 3/3: AI analyzing..."):
        result = subprocess.run([
            ML_PYTHON,
            str(ML_DIR / "forecast_advisor.py"),
            "--products",
            product_ids_str
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"❌ AI Error: {result.stderr}")
            return False
    
    with st.spinner("💾 Saving to database..."):
        saved_count = save_forecasts_to_database()
        if saved_count > 0:
            st.success(f"✅ Saved {saved_count} forecasts to database")
    
    return True

st.markdown("""
<div class="main-header">
    <h1>🔮 AI-Powered Demand Forecasting</h1>
    <p>Select products, add business context, get expert advice</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.show_summary and st.session_state.ai_recommendations:
    recs = st.session_state.ai_recommendations
    
    if recs.get('summary'):
        summary_text = recs['summary'].strip()
        
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown('<div class="summary-title">📊 AI Business Summary</div>', unsafe_allow_html=True)
        st.markdown(summary_text)
        st.markdown('</div>', unsafe_allow_html=True)
        
        col_audio, col_dismiss = st.columns([4, 1])
        
        with col_audio:
            audio_bytes = generate_bangla_audio(summary_text)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
        
        with col_dismiss:
            if st.button("✖ Close", use_container_width=True):
                st.session_state.show_summary = False
                st.rerun()
        
        st.markdown("---")

with st.expander("📝 Add Business Context (Optional but Recommended)", expanded=False):
    st.markdown("""
    Add any extra information that might affect sales:
    - Upcoming events
    - Market changes
    - Customer behavior
    - Competition
    """)
    
    context = st.text_area(
        "Write in Bangla or English:",
        value=st.session_state.external_context,
        placeholder="Example: পরশু ঈদ। মানুষ এখন বেশি চিনি আর তেল কিনছে।",
        height=100
    )
    
    if st.button("💾 Save Context"):
        st.session_state.external_context = context
        st.success("✅ Context saved!")

if len(st.session_state.selected_products) > 0:
    st.info(f"**✓ {len(st.session_state.selected_products)} products selected**")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button(
            f"🔮 Forecast {len(st.session_state.selected_products)} Products Now",
            type="primary",
            use_container_width=True
        ):
            product_ids = list(st.session_state.selected_products)
            success = run_forecast_pipeline(product_ids)
            
            if success:
                forecast_csv = ML_DIR / "data" / "forecast_output.csv"
                if forecast_csv.exists():
                    st.session_state.forecast_results = pd.read_csv(forecast_csv)
                
                rec_json = ML_DIR / "data" / "ai_recommendations.json"
                if rec_json.exists():
                    with open(rec_json, 'r', encoding='utf-8') as f:
                        st.session_state.ai_recommendations = json.load(f)
                
                st.session_state.show_summary = True
                st.success("✅ Forecast complete! Scroll to top for summary.")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.selected_products = set()
            st.rerun()

st.markdown("---")
st.markdown("## 🛍️ Product List")

col1, col2 = st.columns([3, 1])

with col1:
    search = st.text_input(
        "🔍 Search",
        value=st.session_state.search_term,
        placeholder="Product name..."
    )
    st.session_state.search_term = search

with col2:
    if st.button("🔄 Reset"):
        st.session_state.search_term = ""
        st.session_state.current_page = 1
        st.rerun()

all_products = list(db.get_all_products())

if st.session_state.search_term:
    filtered = [p for p in all_products if st.session_state.search_term.lower() in p[1].lower()]
else:
    filtered = all_products

per_page = 25
total_pages = max(1, (len(filtered) + per_page - 1) // per_page)
start = (st.session_state.current_page - 1) * per_page
end = min(start + per_page, len(filtered))
page_products = filtered[start:end]

st.info(f"Page {st.session_state.current_page}/{total_pages} | Showing {start+1}-{end} of {len(filtered)}")

col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
        st.session_state.current_page -= 1
        st.rerun()

with col_next:
    if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages):
        st.session_state.current_page += 1
        st.rerun()

st.markdown("---")

for product in page_products:
    pid, name, category, cost, price, stock = product[:6]
    
    is_selected = pid in st.session_state.selected_products
    
    col1, col2 = st.columns([0.5, 9.5])
    
    with col1:
        selected = st.checkbox("", value=is_selected, key=f"cb_{pid}", label_visibility="collapsed")
        if selected != is_selected:
            if selected:
                st.session_state.selected_products.add(pid)
            else:
                st.session_state.selected_products.discard(pid)
            st.rerun()
    
    with col2:
        st.markdown(f"**{name}** | {category} | Stock: {stock} | ৳{price}")
        
        with st.expander("💡 View Forecast", expanded=False):
            last_forecast = get_last_forecast(pid)
            
            if last_forecast:
                date, advice, profit, reorder, qty = last_forecast
                try:
                    forecast_time = datetime.fromisoformat(date).strftime("%d %b %Y, %I:%M %p")
                except:
                    forecast_time = str(date)
                
                st.markdown(f"**Last forecasted:** {forecast_time}")
                st.markdown(f'<div class="forecast-box">{advice}</div>', unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Forecast (7d)", f"{qty:.1f}")
                col_b.metric("Profit", f"৳{profit:,.0f}")
                col_c.metric("Reorder", f"{reorder:.0f}")
                
                if st.button("🔄 Update Now", key=f"upd_{pid}"):
                    success = run_forecast_pipeline([pid])
                    if success:
                        st.success("✅ Updated!")
                        st.rerun()
            else:
                st.warning("No forecast yet.")
                
                if st.button("🔮 Forecast This Product", key=f"new_{pid}"):
                    success = run_forecast_pipeline([pid])
                    if success:
                        st.success("✅ Done!")
                        st.rerun()

st.markdown("---")

if st.button("🌍 Forecast ALL Products", type="secondary"):
    all_ids = [p[0] for p in all_products]
    
    progress = st.progress(0)
    status = st.empty()
    
    batch_size = 25
    batches = [all_ids[i:i+batch_size] for i in range(0, len(all_ids), batch_size)]
    
    for idx, batch in enumerate(batches):
        status.text(f"Batch {idx+1}/{len(batches)}...")
        run_forecast_pipeline(batch)
        progress.progress((idx + 1) / len(batches))
    
    st.success("✅ All forecasted!")
    st.session_state.show_summary = True
    st.rerun()

if st.session_state.ai_recommendations:
    st.markdown("---")
    st.markdown("## 📦 Product-Specific AI Recommendations")
    
    recs = st.session_state.ai_recommendations
    
    for rec in recs.get('products', []):
        pid = rec['product_id']
        advice = rec.get('advice', '')
        name = next((p[1] for p in all_products if p[0] == pid), f"Product {pid}")
        
        with st.expander(f"📦 {name}"):
            st.markdown(f'<div class="forecast-box">{advice}</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("🔮 Powered by LightGBM + DeepSeek Chimera")
