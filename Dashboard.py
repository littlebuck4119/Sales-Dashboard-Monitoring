import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# API URL สำหรับดึงข้อมูล
API_URL = "https://api.npoint.io/506e2020f13e6d515726"

@st.cache_data(ttl=10)
def get_data_from_api():
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['sync_date'] = pd.to_datetime(df['sync_date'])
            return df
    except:
        return pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

full_df = get_data_from_api()

if not full_df.empty:
    # 1. ดึงรายชื่อสาขาทั้งหมดที่มีประวัติใน API เพื่อสร้างแกน Y
    shop_list = sorted(full_df['shop_name'].unique())
    
    # 2. กรองเฉพาะเดือนที่เลือก
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    # 3. สร้างโครงตาราง
    _, last_day = calendar.monthrange(y, m)
    days_in_month = [i for i in range(1, last_day + 1)]
    grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month, dtype=object)

    # 4. แมป Status ลงในตาราง
    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index and row['Day'] in grid_df.columns:
                grid_df.at[row['shop_name'], row['Day']] = row['status_code']

    # --- ฟังก์ชันการแสดงผล (ตาม Style เดิมของพี่) ---
    def format_status(val):
        if val == 2 or val == 2.0: return "✅"
        if val == 1 or val == 1.0: return "⚠️"
        if val == 0 or val == 0.0: return "❌"
        return "N/A"

    def style_grid(val):
        base = 'background-color: #f8f9fa; text-align: center; border: 1px solid #ffffff;'
        if val == "N/A": return base + ' color: #adb5bd; font-size: 8px;'
        return base

    st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")
    styled_grid = grid_df.style.map(style_grid).format(format_status)

    st.dataframe(styled_grid, use_container_width=True, height=800)
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
else:
    st.warning("⚠️ ไม่พบข้อมูลใน API กรุณารันไฟล์เช็คยอดที่เครื่อง Local ก่อน")
