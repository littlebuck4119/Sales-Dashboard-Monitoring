import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime

# 1. บังคับกาง Sidebar ตั้งแต่เกิด
st.set_page_config(
    page_title="Sales Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ข้อมูล API
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
            df['sync_date'] = pd.to_datetime(df['sync_date'])
            return df
    except: return pd.DataFrame()

# 3. Sidebar (กางรอไว้อยู่แล้ว)
with st.sidebar:
    st.title("📊 Sales Monitor")
    brand = st.selectbox("1. เลือกแบรนด์", ["🛑 กรุณาเลือกแบรนด์ 🛑"] + list(BRAND_CONFIG.keys()))
    
    st.write("---")
    y = st.selectbox("ปี", [2025, 2026], index=1)
    month_list = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน", month_list, index=datetime.now().month-1)
    m = month_list.index(m_name) + 1

# 4. Main Content
if brand == "🛑 กรุณาเลือกแบรนด์ 🛑":
    st.write("#")
    st.info("👈 เริ่มต้นใช้งานโดยการเลือกแบรนด์ที่แถบเมนูด้านซ้ายครับ")
else:
    st.header(f"📈 {brand} ({m_name} {y})")
    df = get_data(f"https://api.npoint.io/{BRAND_CONFIG[brand]}")
    
    if not df.empty:
        # ดึงการตั้งค่า เปิด/ปิด สาขา
        conf = requests.get(CONFIG_API).json().get(brand, {})
        shops = sorted(df['shop_name'].unique())
        
        # สร้างตาราง Heatmap
        mask = (df['sync_date'].dt.month == m) & (df['sync_date'].dt.year == y)
        df_filtered = df[mask].copy()
        _, last_day = calendar.monthrange(y, m)
        grid_df = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

        if not df_filtered.empty:
            df_filtered['Day'] = df_filtered['sync_date'].dt.day
            for s in shops:
                if not conf.get(s, True): grid_df.loc[s] = "DISABLED"
            for _, r in df_filtered.iterrows():
                if r['shop_name'] in grid_df.index and grid_df.at[r['shop_name'], r['Day']] != "DISABLED":
                    grid_df.at[r['shop_name'], r['Day']] = "✅" if r['status_code'] == 2 else "⚠️" if r['status_code'] == 1 else "❌"

        # ระบายสีตาราง
        def style_cells(v):
            if v == "✅": return 'background-color: #d4edda;'
            if v == "⚠️": return 'background-color: #fff3cd;'
            if v == "❌": return 'background-color: #f8d7da;'
            if v == "DISABLED": return 'background-color: #e9ecef; color: #adb5bd;'
            return 'color: #eeeeee;'

        st.dataframe(grid_df.style.applymap(style_cells), use_container_width=True, height=750)
    else:
        st.warning("ไม่พบข้อมูล")
