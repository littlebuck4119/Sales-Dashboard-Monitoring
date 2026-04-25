import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CORE CONFIG & ULTIMATE CSS ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    /* 1. ซ่อน Cursor ทุกจุด */
    * { caret-color: transparent !important; }
    
    /* 2. ซ่อน Header/Footer มาตรฐาน */
    header, footer { visibility: hidden !important; }

    /* 3. ดันปุ่มเปิด Sidebar (ลูกศรมุมซ้าย) ให้ลอยเหนือกราฟิกหน้า Welcome */
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999 !important;
        background-color: rgba(255, 255, 255, 0.5);
        border-radius: 50%;
    }

    /* 4. ปรับแต่งหน้า Welcome ไม่ให้ทับเลเยอร์ปุ่ม */
    .welcome-screen {
        background: #0f172a;
        padding: 80px 40px;
        border-radius: 40px;
        color: white;
        text-align: center;
        max-width: 850px;
        margin: 5vh auto 20px auto;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
        border: 1px solid #1e293b;
        position: relative;
        z-index: 1; /* ต่ำกว่า Sidebar */
    }
    
    /* สไตล์ปุ่ม Get Started */
    .stButton > button {
        background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 45px !important;
        font-weight: 700 !important;
        border-radius: 50px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA UTILS ---
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

# --- 3. SIDEBAR IMPLEMENTATION ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 25px;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: bold;">LAST SYNC</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">{now.strftime("%d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_list, index=0)
    
    col1, col2 = st.columns(2)
    with col1: target_y = st.selectbox("ปี", [2025, 2026], index=1)
    with col2:
        m_names = list(calendar.month_name)[1:]
        m_target_name = st.selectbox("เดือน", m_names, index=now.month-1)
        target_m = m_names.index(m_target_name) + 1
    
    summary_st = st.empty()
    st.markdown("---")

# --- 4. DISPLAY LOGIC ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div class="welcome-screen">
            <div style="font-size: 4.5rem; margin-bottom: 10px;">📊</div>
            <h1 style="font-size: 3.5rem; font-weight: 800; letter-spacing: -2px; margin:0;">Sales Monitoring</h1>
            <div style="width: 50px; height: 4px; background: #38bdf8; margin: 25px auto; border-radius: 10px;"></div>
            <p style="font-size: 1.2rem; color: #94a3b8; margin-bottom: 35px;">
                ระบบติดตามสถานะยอดขายสาขาเรียลไทม์<br>
                กรุณาเลือกแบรนด์จากเมนูทางซ้ายเพื่อเริ่มต้น
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # วางปุ่มใน Main Page เพื่อสะกิดให้ Sidebar ทำงาน
    col_l, col_btn, col_r = st.columns([1, 1.2, 1])
    with col_btn:
        if st.button("📂 OPEN CONTROL PANEL"):
            st.toast("เปิดเมนูที่แถบด้านซ้ายมือ 👈", icon="ℹ️")
    st.stop()

# --- 5. DASHBOARD VIEW ---
st.title(f"📈 {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 การตั้งค่าสาขา", expanded=False):
            query = st_keyup("🔍 ค้นหา...", key=f"f_{selected_brand}").strip().lower()
            
            m_key = f"m_{selected_brand}"
            def sync_all():
                for s in unique_shops: st.session_state[f"tg_{selected_brand}_{s}"] = st.session_state[m_key]
            
            is_all_on = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("เลือกทั้งหมด", value=is_all_on, key=m_key, on_change=sync_all)
            
            new_settings = {}
            for shop in unique_shops:
                if query and query not in shop.lower(): continue
                t_key = f"tg_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                new_settings[shop] = st.toggle(shop, key=t_key)
            
            if st.button("💾 SAVE SETTINGS", use_container_width=True):
                all_configs[selected_brand] = {s: st.session_state.get(f"tg_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("บันทึกแล้ว!")
                st.rerun()

    # Heatmap Logic
    mask = (raw_df['sync_date'].dt.month == target_m) & (raw_df['sync_date'].dt.year == target_y)
    df_filtered = raw_df[mask].copy()
    _, last_day = calendar.monthrange(target_y, target_m)
    heatmap_grid = pd.DataFrame("N/A", index=unique_shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in unique_shops:
            if not current_settings.get(shop, True): heatmap_grid.loc[shop] = "DISABLED"
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in heatmap_grid.index and heatmap_grid.at[row['shop_name'], row['Day']] != "DISABLED":
                stc = row['status_code']
                heatmap_grid.at[row['shop_name'], row['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    def cell_style(v):
        if v == "✅": return 'background-color: #dcfce7; color: #166534;'
        if v == "⚠️": return 'background-color: #fef9c3; color: #854d0e;'
        if v == "❌": return 'background-color: #fee2e2; color: #991b1b;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #cbd5e1;'

    st.dataframe(heatmap_grid.style.map(cell_style), use_container_width=True, height=750)
else:
    st.warning("ไม่มีข้อมูล")
