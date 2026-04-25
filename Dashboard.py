import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG (ตั้งค่าพื้นฐานที่สุด) ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # บังคับกาง Sidebar
)

# --- 2. ONLY CURSOR HIDER (ไม่มี CSS จัดหน้าตาแล้ว) ---
st.markdown("""
    <style>
    /* ซ่อนขีดกระพริบตามความต้องการหลัก */
    * { caret-color: transparent !important; }
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

# --- 4. SIDEBAR (กางออกมาแน่นอน) ---
with st.sidebar:
    st.title("Main Menu")
    now = datetime.now()
    st.write(f"วันที่: {now.strftime('%d/%m/%Y')}")
    
    brand_list = ["-- เลือกแบรนด์ --"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_list)
    
    y = st.selectbox("ปี", [2025, 2026], index=1)
    m_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน", m_names, index=now.month-1)
    m = m_names.index(m_name) + 1
    st.markdown("---")

# --- 5. MAIN CONTENT ---
if selected_brand == "-- เลือกแบรนด์ --":
    st.title("Dashboard Monitoring")
    st.write("👈 กรุณาเลือกแบรนด์ที่เมนูทางซ้ายมือ")
    st.stop()

# --- 6. DASHBOARD VIEW ---
st.title(f"📊 {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("ตั้งค่าเปิด/ปิด สาขา", expanded=False):
            search = st_keyup("🔍 ค้นหา...", key=f"s_{selected_brand}").strip().lower()
            
            is_all = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("เปิดทั้งหมด", value=is_all, key=f"all_{selected_brand}")
            
            for shop in unique_shops:
                if search and search not in shop.lower(): continue
                t_key = f"t_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                st.toggle(shop, key=t_key)
            
            if st.button("บันทึกการตั้งค่า", type="primary"):
                all_configs[selected_brand] = {s: st.session_state.get(f"t_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("บันทึกสำเร็จ")
                st.rerun()

    # ตาราง Heatmap
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

    def cell_style(v):
        if v == "✅": return 'background-color: #d4edda;'
        if v == "⚠️": return 'background-color: #fff3cd;'
        if v == "❌": return 'background-color: #f8d7da;'
        if v == "DISABLED": return 'background-color: #eee; color: transparent;'
        return 'color: #ccc;'

    st.dataframe(grid.style.map(cell_style), use_container_width=True, height=700)
else:
    st.warning("ไม่มีข้อมูล")
