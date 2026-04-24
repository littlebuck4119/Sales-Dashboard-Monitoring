import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG: บังคับกาง Sidebar ตั้งแต่เริ่ม ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # กางออกมาเลย ไม่ต้องรอคลิก
)

# --- 2. CSS: เน้นให้อ่านง่าย สะอาดตา ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA API ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

@st.cache_data(ttl=30)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
            df['sync_date'] = pd.to_datetime(df['sync_date'])
            return df
    except: return pd.DataFrame()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📊 Sales Monitor")
    now = datetime.now()
    st.info(f"Today: {now.strftime('%d %b %Y')}")
    
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_options, index=0)
    
    st.markdown("---")
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # ถ้ายังไม่เลือกแบรนด์ ให้บอก User ชัดๆ
    st.write("#")
    st.write("#")
    st.markdown("<h1 style='text-align: center; color: #6c757d;'>👈 กรุณาเลือกแบรนด์ที่แถบเมนูซ้ายมือ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #adb5bd;'>โปรแกรมจะแสดงข้อมูล Heatmap ทันทีเมื่อเลือกแบรนด์</p>", unsafe_allow_html=True)
else:
    st.header(f"📈 Dashboard: {selected_brand}")
    full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

    if not full_df.empty:
        # ดึง Config การเปิด/ปิดสาขา
        brand_settings = requests.get(CONFIG_API).json().get(selected_brand, {})
        shops = sorted(full_df['shop_name'].unique())
        
        # เตรียมตาราง Heatmap
        mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
        df_filtered = full_df[mask].copy()
        _, last_day = calendar.monthrange(y, m)
        days = list(range(1, last_day + 1))
        grid_df = pd.DataFrame("N/A", index=shops, columns=days)

        if not df_filtered.empty:
            df_filtered['Day'] = df_filtered['sync_date'].dt.day
            for shop in shops:
                if not brand_settings.get(shop, True): grid_df.loc[shop] = "DISABLED"
            for _, row in df_filtered.iterrows():
                sn, dy, sc = row['shop_name'], row['Day'], row['status_code']
                if sn in grid_df.index and grid_df.at[sn, dy] != "DISABLED":
                    grid_df.at[sn, dy] = "✅" if sc == 2 else "⚠️" if sc == 1 else "❌"
        
        # สรุปผลลง Sidebar
        with sidebar_summary.container():
            st.success(f"โหลดข้อมูลสาขาเรียบร้อย")
            active_list = [s for s in shops if brand_settings.get(s, True)]
            st.metric("สาขาที่เปิดใช้", f"{len(active_list)} / {len(shops)}")

        # ฟังก์ชันระบายสี
        def apply_style(val):
            if val == "✅": return 'background-color: #d4edda; color: #155724; text-align: center;'
            if val == "⚠️": return 'background-color: #fff3cd; color: #856404; text-align: center;'
            if val == "❌": return 'background-color: #f8d7da; color: #721c24; text-align: center;'
            if val == "DISABLED": return 'background-color: #e9ecef; color: #dee2e6;'
            return 'color: #f8f9fa;'

        st.dataframe(grid_df.style.applymap(apply_style), use_container_width=True, height=700)
    else:
        st.warning("⚠️ ไม่พบข้อมูลสำหรับเดือน/ปี ที่เลือก")
