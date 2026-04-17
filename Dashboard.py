import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIG (ใช้ Format สวยๆ จากไฟล์ Dashboard.py ของพี่) ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

API_ID = "506e2020f13e6d515726"
API_URL = "https://api.npoint.io/" + API_ID

@st.cache_data(ttl=10)
def get_data(year, month):
    try:
        # เปลี่ยนมาดึงจาก API แทนการดึงจาก IP 203.xxx
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # ปรับชื่อคอลัมน์ให้ตรงกับที่ Dashboard เดิมต้องการ
            df.rename(columns={'shop_name': 'Shop', 'sync_date': 'Date', 'status_code': 'Status'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            mask = (df['Date'].dt.month == month) & (df['Date'].dt.year == year)
            return df[mask]
    except:
        pass
    return pd.DataFrame()

# --- UI และการแสดงผล (ตามเดิมของพี่เป๊ะๆ) ---
st.title("📊 Eat Am Are - Sales Monitoring Heatmap")

with st.sidebar:
    st.header("ตัวเลือก")
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    m_name = st.selectbox("เดือน (Month)", list(calendar.month_name)[1:], index=datetime.now().month-1)
    m = list(calendar.month_name).index(m_name)

df = get_data(y, m)

# ... (Logic การวาดตารางและสไตล์ตารางใช้ตามไฟล์ Dashboard.py เดิมของพี่เลยครับ) ...
