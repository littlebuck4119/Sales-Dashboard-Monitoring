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

@st.cache_data(ttl=5) # ตั้ง Cache สั้นๆ เพื่อให้เห็นข้อมูลใหม่ทันที
def get_data(year, month):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        # 1. ดึงข้อมูล Log
        query_log = f"""
            SELECT shop_name as Shop, sync_date as Date, status_code as Status 
            FROM monitor_sync_log 
            WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}
        """
        df_log = pd.read_sql(query_log, conn)
        
        # 2. ดึงรายชื่อสาขา (Master)
        query_shops = "SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND deleted=0 AND ismonitorsales=1"
        df_shops = pd.read_sql(query_shops, conn)
        
        conn.close()
        return df_log, df_shops
    except Exception as e:
        # หากต่อ DB ไม่ได้ ให้แสดง Error แจ้งเตือน
        st.error(f"⚠️ การเชื่อมต่อฐานข้อมูลขัดข้อง: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- UI ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

df_log, df_shops = get_data(y, m)

# --- จัดการรายชื่อร้าน (Shop List) ---
# หากดึงจากตาราง productlevel ไม่ได้ ให้ดึงจากข้อมูลที่มีใน log แทน
if not df_shops.empty:
    shop_list = sorted(df_shops['ProductLevelName'].unique())
elif not df_log.empty:
    shop_list = sorted(df_log['Shop'].unique())
else:
    shop_list = []

# --- เตรียมคอลัมน์วันที่ ---
_, last_day = calendar.monthrange(y, m)
days_in_month = [str(i) for i in range(1, last_day + 1)]

# --- สร้างตารางโครงร่าง (Empty Grid) ---
grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month)

# --- นำข้อมูลจาก Log มาใส่ในตาราง ---
if not df_log.empty and shop_list:
    # สำคัญ: แปลงวันที่จากฐานข้อมูลให้เป็น String เพื่อให้ตรงกับหัวคอลัมน์
    df_log['Day'] = pd.to_datetime(df_log['Date']).dt.day.astype(str)
    
    for _, row in df_log.iterrows():
        s_name = row['Shop']
        s_day = row['Day']
        s_status = row['Status']
        
        if s_name in grid_df.index and s_day in grid_df.columns:
            # เก็บค่าเป็นตัวเลขเพื่อให้ฟังก์ชัน Style ตรวจจับสีได้
            try:
                grid_df.at[s_name, s_day] = int(s_status)
            except:
                grid_df.at[s_name, s_day] = s_status

# --- ฟังก์ชันการแสดงผล ---
def format_status(val):
    if val == 2 or val == "2": return "✅"
    if val == 1 or val == "1": return "⚠️"
    if val == 0 or val == "0": return "❌"
    return "N/A"

def style_grid(val):
    # จัดการสีพื้นหลังตามสถานะ
    base = 'text-align: center; font-size: 11px; border: 1px solid #eee;'
    if val == 2 or val == "2": return base + 'background-color: #2e7d32; color: white;' # เขียว
    if val == 1 or val == "1": return base + 'background-color: #fbc02d; color: black;' # เหลือง
    if val == 0 or val == "0": return base + 'background-color: #d32f2f; color: white;' # แดง
    return base + 'background-color: #ffffff; color: #adb5bd;' # N/A (ไม่มีข้อมูล)

# --- การแสดงตารางบนหน้าเว็บ ---
if not shop_list:
    st.warning("🔍 ไม่พบข้อมูลร้านค้าในฐานข้อมูล กรุณาตรวจสอบการเชื่อมต่อหรือข้อมูลใน monitor_sync_log")
else:
    st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")
    
    st.dataframe(
        grid_df.style.map(style_grid).format(format_status), 
        use_container_width=True, 
        height=800,
        column_config={d: st.column_config.Column(width=35) for d in days_in_month}
    )

st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
