import streamlit as st
import pandas as pd
import pymysql
import calendar
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")
DB_CONFIG = {
    "host": "203.154.140.85", "user": "POSAdmin", "password": "pospwnet", 
    "database": "eat_am_are_hq", "port": 3307, "charset": "utf8"
}

@st.cache_data(ttl=60)
def get_data(year, month):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = f"SELECT shop_name as Shop, sync_date as Date, status_code as Status FROM monitor_sync_log WHERE MONTH(sync_date) = {month} AND YEAR(sync_date) = {year}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except: return pd.DataFrame()

# UI & Processing
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")
y = datetime.now().year
m = datetime.now().month
df = get_data(y, m)

# ดึงรายชื่อสาขา
try:
    conn = pymysql.connect(**DB_CONFIG)
    shop_list = sorted(pd.read_sql("SELECT ProductLevelName FROM productlevel WHERE isshop=1 AND ismonitorsales=1", conn)['ProductLevelName'].tolist())
    conn.close()
except: shop_list = sorted(df['Shop'].unique().tolist()) if not df.empty else []

# สร้าง Grid ตาราง (ใช้คอลัมน์เป็น String เพื่อให้ Map ข้อมูลแม่นยำ)
num_days = calendar.monthrange(y, m)[1]
grid_df = pd.DataFrame("N/A", index=shop_list, columns=[str(i) for i in range(1, num_days + 1)])

if not df.empty:
    df['Day'] = pd.to_datetime(df['Date']).dt.day.astype(str)
    for _, row in df.iterrows():
        if row['Shop'] in grid_df.index and row['Day'] in grid_df.columns:
            grid_df.at[row['Shop'], row['Day']] = int(row['Status'])

def format_status(val):
    return "✅" if val == 2 else ("⚠️" if val == 1 else ("❌" if val == 0 else " "))

def style_grid(val):
    if val == 2: return 'background-color: #2e7d32; color: white; text-align: center;'
    if val == 1: return 'background-color: #fbc02d; color: black; text-align: center;'
    if val == 0: return 'background-color: #d32f2f; color: white; text-align: center;'
    return 'background-color: #f8f9fa; color: #ddd; text-align: center;'

st.dataframe(grid_df.style.map(style_grid).format(format_status), use_container_width=True, height=800)
