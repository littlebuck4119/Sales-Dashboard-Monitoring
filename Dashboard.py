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
        query = f"""
            SELECT shop_name as Shop, sync_date as Date, status_code as Status 
            FROM monitor_sync_log 
            WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df = get_data(y, m)

# 1. คำนวณหาจำนวนวันในเดือนที่เลือก (อิงตามปฏิทินจริง)
_, last_day = calendar.monthrange(y, m)
days_in_month = [i for i in range(1, last_day + 1)]

# 2. ดึงรายชื่อสาขา
try:
    conn = pymysql.connect(**DB_CONFIG)
    all_shops = pd.read_sql("SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND deleted=0 AND ismonitorsales=1", conn)
    conn.close()
    shop_list = sorted(all_shops['ProductLevelName'].tolist())
except:
    shop_list = sorted(df['Shop'].unique()) if not df.empty else []

# 3. สร้างโครงตาราง (ใช้ dtype=object เพื่อป้องกัน TypeError เลข '2')
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month, dtype=object)

# 4. นำข้อมูล Status มาวางทับ (ถ้ามี)
if not df.empty:
    df['Day'] = pd.to_datetime(df['Date']).dt.day
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            grid_df.at[row['Shop'], row['Day']] = row['Status']

# 5. ฟังก์ชันจัดการการแสดงผล
def format_status(val):
    if val == 2 or val == 2.0: return "✅"
    if val == 1 or val == 1.0: return "⚠️"
    if val == 0 or val == 0.0: return "❌"
    return "N/A"

def style_grid(val):
    base_style = 'background-color: #f8f9fa; text-align: center; border: 1px solid #ffffff;'
    if val == "N/A":
        return base_style + ' color: #adb5bd; font-size: 8px;'
    return base_style

# --- ส่วนการแสดงผลตาราง ---
st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")

styled_grid = grid_df.style.map(style_grid).format(format_status)

st.dataframe(
    styled_grid, 
    use_container_width=True, 
    height=800,
    column_config={
        str(i): st.column_config.Column(label=str(i), width=15) for i in days_in_month
    }
)

# 6. แก้ไขจุด Error: ใช้ st.html แทน st.markdown สำหรับ CSS ใน Streamlit รุ่นใหม่
st.html("""
<style>
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        padding: 0px !important;
        min-width: 15px !important;
        max-width: 28px !important;
    }
    div[data-testid="stTable"] td {
        font-size: 10px !important;
    }
    .stDataFrame { overflow-x: hidden !important; }
</style>
""")

st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
