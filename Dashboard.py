import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# CSS สำหรับหดช่องตารางให้เล็กลงที่สุด เพื่อให้อยู่ในหน้าเดียว
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { font-size: 10px; }
    div[data-testid="stDataFrame"] > div { width: 100% !important; }
    th, td { padding: 2px !important; text-align: center !important; min-width: 25px !important; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://api.npoint.io/506e2020f13e6d515726"

@st.cache_data(ttl=10)
def get_data_from_api():
    try:
        res = requests.get(API_URL, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

st.title("📊 Eat Am Are - Sales Monitoring Heatmap")
with st.sidebar:
    y = st.selectbox("ปี", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_data_from_api()
if not df.empty:
    df['sync_date'] = pd.to_datetime(df['sync_date'])
    shop_list = sorted(df['shop_name'].unique())
    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    
    grid_df = pd.DataFrame("N/A", index=shop_list, columns=days)
    mask = (df['sync_date'].dt.month == m) & (df['sync_date'].dt.year == y)
    df_f = df[mask].copy()
    
    for _, row in df_f.iterrows():
        d = row['sync_date'].day
        if row['shop_name'] in grid_df.index and d in grid_df.columns:
            grid_df.at[row['shop_name'], d] = row['status_code']

    def format_status(val):
        if val == 2 or val == 2.0: return "✅"
        if val == 1 or val == 1.0: return "⚠️"
        if val == 0 or val == 0.0: return "❌"
        return " " # ใช้ช่องว่างแทน N/A เพื่อความประหยัดเนื้อที่

    st.subheader(f"🗓️ {m_name} {y}")
    # แสดงผลตารางแบบหดช่อง
    st.dataframe(grid_df.style.format(format_status), use_container_width=True, height=800)
