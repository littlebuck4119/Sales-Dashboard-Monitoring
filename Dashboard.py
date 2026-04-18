import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# =========================================================
# 1. เพิ่มสมุดรายชื่อแบรนด์ (พี่มาเพิ่มร้านใหม่ตรงนี้ได้เลย)
# =========================================================
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee",
    "ร้านที่ 3": "ID_3",
}

# --- UI Sidebar ---
with st.sidebar:
    st.header("ตัวเลือก")
    
    # --- ส่วนที่เพิ่ม: สลับแบรนด์ ---
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    # เปลี่ยน API_URL ตามแบรนด์ที่เลือก
    API_URL = f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}"
    
    st.divider()
    
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

# --- หัวข้อหน้าเว็บ (เปลี่ยนตามแบรนด์ที่เลือก) ---
st.title(f"📊 {selected_brand} - Sales Monitoring Heatmap")

@st.cache_data(ttl=10)
def get_data_from_api(url): # รับ url เป็น parameter เพื่อให้ดึงใหม่เวลาสลับแบรนด์
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['sync_date'] = pd.to_datetime(df['sync_date'])
            return df
    except:
        return pd.DataFrame()

# เรียกใช้ฟังก์ชันโดยส่ง API_URL ของแบรนด์ที่เลือกเข้าไป
full_df = get_data_from_api(API_URL)

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

    # --- ฟังก์ชันการแสดงผล (ใช้ตาม Style เดิมของพี่เป๊ะๆ) ---
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
    
    # ส่วนของตารางและการจัด Format
    styled_grid = grid_df.style.map(style_grid).format(format_status)

    # แสดงผลตาราง (ใช้ขนาดเดิม 800)
    st.dataframe(styled_grid, use_container_width=True, height=800)
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
else:
    st.warning(f"⚠️ ไม่พบข้อมูลของ {selected_brand} ใน API กรุณาเช็คการรันไฟล์ที่เครื่อง Local")
