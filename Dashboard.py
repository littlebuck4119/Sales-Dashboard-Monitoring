import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime
import calendar

st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

DB_CONFIG = {
    "host": "203.154.140.85", "user": "POSAdmin", "password": "pospwnet", 
    "database": "eat_am_are_hq", "port": 3307, "charset": "utf8"
}

@st.cache_data(ttl=10)
def get_data(year, month):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = f"SELECT shop_name as Shop, sync_date as Date, status_code as Status FROM monitor_sync_log WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}"
        df = pd.read_sql(query, conn); conn.close()
        return df
    except: return pd.DataFrame()

st.title("📊 Eat Am Are - Sales Monitoring Heatmap")
with st.sidebar:
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_data(y, m)
_, last_day = calendar.monthrange(y, m)
# สำคัญ: ต้องเป็น String เพื่อให้ตรงกับ column_config และไม่หายบน Cloud
days_in_month = [str(i) for i in range(1, last_day + 1)]

try:
    conn = pymysql.connect(**DB_CONFIG)
    shop_list = sorted(pd.read_sql("SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND deleted=0 AND ismonitorsales=1", conn)['ProductLevelName'].tolist())
    conn.close()
except: shop_list = sorted(df['Shop'].unique()) if not df.empty else []

# สร้างโครงตาราง
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month)

if not df.empty:
    df['Day'] = pd.to_datetime(df['Date']).dt.day.astype(str) # Match กับ days_in_month (str)
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            grid_df.at[row['Shop'], row['Day']] = int(row['Status'])

def format_status(val):
    if val == 2: return "✅"
    if val == 1: return "⚠️"
    if val == 0: return "❌"
    return "N/A"

def style_grid(val):
    base = 'text-align: center; font-size: 11px; border: 1px solid #eee;'
    if val == 2: return base + 'background-color: #2e7d32; color: white;' # เขียว
    if val == 1: return base + 'background-color: #fbc02d; color: black;' # เหลือง
    if val == 0: return base + 'background-color: #d32f2f; color: white;' # แดง
    return base + 'background-color: #ffffff; color: #adb5bd;' # N/A

st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")

# แสดงผลโดยระบุความกว้างคอลัมน์ให้ชัดเจนเพื่อป้องกันชื่อ Shop หาย
st.dataframe(
    grid_df.style.map(style_grid).format(format_status), 
    use_container_width=True, height=800,
    column_config={d: st.column_config.Column(width=35) for d in days_in_month}
)
st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
