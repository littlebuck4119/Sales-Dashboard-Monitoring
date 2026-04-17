import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")
API_URL = "https://api.npoint.io/506e2020f13e6d515726"

@st.cache_data(ttl=10)
def get_data_from_api():
    try:
        res = requests.get(API_URL, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")
with st.sidebar:
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_data_from_api()

if not df.empty:
    df['sync_date'] = pd.to_datetime(df['sync_date'])
    shop_list = sorted(df['shop_name'].unique())
    _, last_day = calendar.monthrange(y, m)
    days = [i for i in range(1, last_day + 1)]
    
    grid_df = pd.DataFrame("N/A", index=shop_list, columns=days, dtype=object)
    
    mask = (df['sync_date'].dt.month == m) & (df['sync_date'].dt.year == y)
    df_filtered = df[mask].copy()
    
    for _, row in df_filtered.iterrows():
        d = row['sync_date'].day
        if row['shop_name'] in grid_df.index and d in grid_df.columns:
            grid_df.at[row['shop_name'], d] = row['status_code']

    def format_status(val):
        if val == 2 or val == 2.0: return "✅"
        if val == 1 or val == 1.0: return "⚠️"
        if val == 0 or val == 0.0: return "❌"
        return "N/A"

    st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")
    st.dataframe(grid_df.style.format(format_status), use_container_width=True, height=800)
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ไม่มีข้อมูล")
