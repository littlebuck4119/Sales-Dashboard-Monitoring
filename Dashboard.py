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

@st.cache_data(ttl=10)
def get_data(year, month):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = f"SELECT shop_name as Shop, sync_date as Date, status_code as Status FROM monitor_sync_log WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except: return pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_data(y, m)
_, last_day = calendar.monthrange(y, m)
# ใช้เลขวันที่ 1-31 เป็นหัว Column
days_in_month = [i for i in range(1, last_day + 1)]

# ดึงรายชื่อสาขา
try:
    conn = pymysql.connect(**DB_CONFIG)
    all_shops = pd.read_sql("SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND deleted=0 AND ismonitorsales=1", conn)
    conn.close()
    shop_list = sorted(all_shops['ProductLevelName'].tolist())
except: 
    shop_list = sorted(df['Shop'].unique()) if not df.empty else []

# สร้างโครงตารางเริ่มต้นด้วย "N/A" เหมือนในรูปต้นฉบับ
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month)

# นำข้อมูลจาก DB มาใส่ในตาราง
if not df.empty:
    df['Day'] = pd.to_datetime(df['Date']).dt.day
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            grid_df.at[row['Shop'], row['Day']] = int(row['Status'])

def format_status(val):
    if val == 2: return "✅"
    if val == 1: return "⚠️"
    if val == 0: return "❌"
    return "N/A" # แสดง N/A สำหรับช่องที่ไม่มีข้อมูลเหมือนในรูป

def style_grid(val):
    # สไตล์พื้นฐาน: ตัวอักษรเล็กลง สีจางลงสำหรับ N/A
    base = 'text-align: center; font-size: 11px;'
    if val == "N/A":
        return base + ' color: #adb5bd; background-color: #ffffff;'
    # ถ้ามีข้อมูล (เป็นตัวเลขสถานะ) ให้ทำพื้นหลังสีขาวแต่ตัวอักษรเข้ม
    return base + ' background-color: #ffffff;'

st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")

# แสดงผลด้วย st.dataframe พร้อมบีบความกว้าง Column
st.dataframe(
    grid_df.style.map(style_grid).format(format_status), 
    use_container_width=True, 
    height=800,
    column_config={
        # วนลูปบีบความกว้างทุก Column วันที่ให้เล็กที่สุด (30-40 pixels)
        day: st.column_config.Column(width=40) for day in days_in_month
    }
)

st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
