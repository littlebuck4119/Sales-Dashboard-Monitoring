import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG มาตรฐานที่สุด ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # บังคับกาง Sidebar ทันที
)

# --- 2. CSS เฉพาะซ่อน Cursor เท่านั้น ---
st.markdown("""
    <style>
    /* ซ่อน Cursor กระพริบถาวร */
    * { caret-color: transparent !important; }
    
    /* ซ่อน Header/Footer ปกติ */
    header, footer { visibility: hidden !important; }

    /* ปรับแต่ง Sidebar ให้เห็นชัดๆ ว่ามาแล้ว */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA UTILS ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

def get_config():
    try:
        res = requests.get(CONFIG_API, timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_config(full_config):
    requests.post(CONFIG_API, json=full_config)

@st.cache_data(ttl=30)
def fetch_api_data(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
                df['sync_date'] = pd.to_datetime(df['sync_date'])
                return df
    except: pass
    return pd.DataFrame()

# --- 4. SIDEBAR (เมนูด้านซ้าย) ---
with st.sidebar:
    st.header("📊 Monitoring Menu")
    now = datetime.now()
    
    # แสดงวันที่แบบเรียบง่าย
    st.info(f"วันที่ปัจจุบัน: {now.strftime('%d/%m/%Y')}")
    
    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("1. เลือกแบรนด์", brand_list, index=0)
    
    y = st.selectbox("2. เลือกปี", [2025, 2026], index=1)
    m_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("3. เลือกเดือน", m_names, index=now.month-1)
    m = m_names.index(m_name) + 1
    
    st.markdown("---")

# --- 5. MAIN CONTENT ---
st.title("Sales Monitoring Dashboard")

if selected_brand == "🛑 SELECT BRAND 🛑":
    st.warning("👈 กรุณาเลือกแบรนด์ที่แถบเมนูด้านซ้ายมือเพื่อดูข้อมูล")
    st.stop()

# --- 6. DASHBOARD เมื่อเลือกแบรนด์แล้ว ---
st.subheader(f"📍 กำลังดูข้อมูล: {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    # ส่วนจัดการสาขาใน Sidebar
    with st.sidebar:
        with st.expander("🚫 ตั้งค่าการ เปิด/ปิด สาขา", expanded=False):
            query = st_keyup("🔍 ค้นหาสาขา...", key=f"f_{selected_brand}").strip().lower()
            
            m_key = f"m_{selected_brand}"
            def sync_all():
                for s in unique_shops: st.session_state[f"tg_{selected_brand}_{s}"] = st.session_state[m_key]
            
            is_all_on = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("เลือกทั้งหมด", value=is_all_on, key=m_key, on_change=sync_all)
            
            for shop in unique_shops:
                if query and query not in shop.lower(): continue
                t_key = f"tg_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                st.toggle(shop, key=t_key)
            
            if st.button("💾 บันทึกตั้งค่าสาขา", use_container_width=True, type="primary"):
                all_configs[selected_brand] = {s: st.session_state.get(f"tg_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("บันทึกแล้ว!")
                st.rerun()

    # จัดการข้อมูลตาราง Heatmap
    mask = (raw_df['sync_date'].dt.month == m) & (raw_df['sync_date'].dt.year == y)
    df_f = raw_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid = pd.DataFrame("N/A", index=unique_shops, columns=range(1, last_day + 1))

    if not df_f.empty:
        df_f['Day'] = df_f['sync_date'].dt.day
        for s in unique_shops:
            if not current_settings.get(s, True): grid.loc[s] = "DISABLED"
        for _, r in df_f.iterrows():
            if r['shop_name'] in grid.index and grid.at[r['shop_name'], r['Day']] != "DISABLED":
                stc = r['status_code']
                grid.at[r['shop_name'], r['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    # Styling ตาราง
    def style_cells(v):
        if v == "✅": return 'background-color: #d4edda; color: #155724;'
        if v == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if v == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;'
        return 'color: #ccc;'

    st.dataframe(grid.style.map(style_cells), use_container_width=True, height=700)
else:
    st.error("ไม่พบข้อมูลสำหรับช่วงเวลาที่เลือก")
