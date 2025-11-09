import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(page_title="CSV Sales Import", page_icon="📥", layout="wide")

@st.cache_resource
def get_db():
    return DatabaseManager()
db = get_db()

st.title("📥 বিক্রয় CSV থেকে ইনপোর্ট")
st.info("এখানে আপনার তৈরি বড় সেলস CSV ফাইল আপলোড করুন। সব তথ্য আপনার লাইভ ডেটাবেজে চলে যাবে। (স্টক পরিবর্তন হবে না)")

uploaded_file = st.file_uploader("CSV ফাইল আপলোড করুন", type=["csv"])
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        required = ['customer_name','customer_phone','product_name','quantity','unit_price','discount','paid_amount','sale_date']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"ফাইলের কিছু প্রয়োজনীয় কলাম নেই: {missing}")
        else:
            st.success(f"{len(df)}টি রেকর্ড প্রস্তুত।")
            with st.expander("প্রিভিউ (প্রথম ১০টি)"):
                st.dataframe(df.head(10))
            if st.button("⚡ ডেটা ইমপোর্ট করুন!", type="primary"):
                prog = st.progress(0)
                ok, fail, errors = 0, 0, []
                for idx, row in df.iterrows():
                    try:
                        res, msg = db.add_bulk_sale_from_csv(
                            customer_name=row['customer_name'],
                            customer_phone=str(row['customer_phone']) if pd.notna(row['customer_phone']) else "",
                            product_name=row['product_name'],
                            quantity=int(row['quantity']),
                            unit_price=float(row['unit_price']),
                            discount=float(row['discount']) if pd.notna(row['discount']) else 0,
                            paid_amount=float(row['paid_amount']),
                            sale_date=str(row['sale_date'])
                        )
                        if res:
                            ok += 1
                        else:
                            fail += 1
                            if len(errors) < 10: errors.append(f"Line {idx+2}: {msg}")
                    except Exception as e:
                        fail += 1
                        if len(errors) < 10: errors.append(f"Line {idx+2}: {e}")
                    if (idx+1) % 50 == 0 or (idx+1) == len(df):
                        prog.progress((idx+1)/len(df))
                prog.empty()
                st.success(f"✅ সফল: {ok:,} | ❗ ব্যর্থ: {fail:,}")
                if errors:
                    st.warning("কিছু ত্রুটি পাওয়া গেছে:")
                    for e in errors:
                        st.caption(e)
                st.balloons()
    except Exception as e:
        st.error(f"ফাইল পড়তে সমস্যা: {e}")

