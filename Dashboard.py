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
# ใช้หัวคอลัมน์เป็น String เพื่อให้ตรงกับ column_config และแก้ปัญหา empty บน Cloud
days_in_month = [str(i) for i in range(1, last_day + 1)]

# ดึงรายชื่อสาขา
try:
    conn = pymysql.connect(**DB_CONFIG)
    all_shops = pd.read_sql("SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND deleted=0 AND ismonitorsales=1", conn)
    conn.close()
    shop_list = sorted(all_shops['ProductLevelName'].tolist())
except: 
    shop_list = sorted(df['Shop'].unique()) if not df.empty else []

# สร้างโครงตาราง (ใช้ dtype=object เพื่อความยืดหยุ่น)
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month, dtype=object)

if not df.empty:
    df['Day'] = pd.to_datetime(df['Date']).dt.day.astype(str)
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            # เก็บค่าเป็นตัวเลขเพื่อให้ style_grid เช็คสีได้ง่าย
            grid_df.at[row['Shop'], row['Day']] = int(row['Status'])

def format_status(val):
    if val == 2: return "✅"
    if val == 1: return "⚠️"
    if val == 0: return "❌"
    return "N/A"

def style_grid(val):
    # กำหนดสีพื้นหลังตามสถานะ (Heatmap Style)
    base = 'text-align: center; font-size: 11px; border: 1px solid #eee;'
    if val == 2: return base + 'background-color: #2e7d32; color: white;' # เขียว
    if val == 1: return base + 'background-color: #fbc02d; color: black;' # เหลือง
    if val == 0: return base + 'background-color: #d32f2f; color: white;' # แดง
    return base + 'background-color: #ffffff; color: #adb5bd;' # N/A

st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")

# แสดงผลโดยใช้ column_config บีบขนาดวันที่ให้เล็ก (กว้าง 35px)
st.dataframe(
    grid_df.style.map(style_grid).format(format_status), 
    use_container_width=True, 
    height=800,
    column_config={
        day: st.column_config.Column(width=35) for day in days_in_month
    }
)

st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
