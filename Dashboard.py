import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime
import calendar

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

DB_CONFIG = {
    "host": "203.154.140.85", 
    "user": "POSAdmin", 
    "password": "pospwnet", 
    "database": "eat_am_are_hq", 
    "port": 3307, 
    "charset": "utf8"
}

@st.cache_data(ttl=5)
def get_dashboard_data(year, month):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        # ดึงข้อมูลจากตาราง log โดยตรง
        query = f"""
            SELECT shop_name as Shop, sync_date as Date, status_code as Status 
            FROM monitor_sync_log 
            WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ เชื่อมต่อฐานข้อมูลไม่ได้: {e}")
        return pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_dashboard_data(y, m)

# 1. เตรียมรายชื่อร้านจากข้อมูลที่มีใน Log (แก้ปัญหาชื่อร้านหาย)
if not df.empty:
    shop_list = sorted(df['Shop'].unique())
else:
    shop_list = []

# 2. เตรียมคอลัมน์วันที่
_, last_day = calendar.monthrange(y, m)
days_in_month = [i for i in range(1, last_day + 1)]

# 3. สร้างโครงตาราง (Empty Grid)
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month)

# 4. นำ Status มาใส่ (แปลงวันที่เป็นตัวเลขเพื่อ Match คอลัมน์)
if not df.empty and shop_list:
    df['Day'] = pd.to_datetime(df['Date']).dt.day
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            grid_df.at[row['Shop'], row['Day']] = row['Status']

# 5. ฟังก์ชันแสดงผล (สัญลักษณ์และสี)
def format_status(val):
    try:
        v = int(float(val))
        if v == 2: return "✅"
        if v == 1: return "⚠️"
        if v == 0: return "❌"
    except: pass
    return "N/A"

def style_grid(val):
    # กำหนดสีพื้นหลัง (เขียว/เหลือง/แดง)
    try:
        v = int(float(val))
        if v == 2: return 'background-color: #2e7d32; color: white; text-align: center;'
        if v == 1: return 'background-color: #fbc02d; color: black; text-align: center;'
        if v == 0: return 'background-color: #d32f2f; color: white; text-align: center;'
    except: pass
    return 'color: #adb5bd; text-align: center;'

# --- แสดงผล ---
if not shop_list:
    st.warning("🔍 ไม่พบข้อมูลในเดือนที่เลือก (ตรวจสอบว่า monitor_sync_log มีข้อมูลของเดือนนี้หรือไม่)")
else:
    st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")
    
    # ใช้ st.dataframe พร้อมจัดสี
    st.dataframe(
        grid_df.style.map(style_grid).format(format_status), 
        use_container_width=True, 
        height=800,
        column_config={i: st.column_config.Column(width=35) for i in days_in_month}
    )

st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
