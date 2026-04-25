import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SIDEBAR STATE CONTROL ---
# ใช้ Query Param เพื่อบังคับสถานะ Sidebar ให้ชัวร์ 100%
if "nav" not in st.query_params:
    st.query_params["nav"] = "closed"

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    # ถ้า nav เป็น open ให้กาง Sidebar ทันที
    initial_sidebar_state="expanded" if st.query_params["nav"] == "open" else "collapsed"
)

# --- 2. THEME & CURSOR KILLER ---
st.markdown("""
    <style>
    /* ฆ่า Cursor กระพริบถาวร */
    * { caret-color: transparent !important; }
    
    /* ซ่อน Header/Footer */
    header, footer { visibility: hidden !important; }

    /* ปรับแต่งปุ่ม OPEN CONTROL PANEL ให้เด่นสุดๆ */
    div.stButton > button {
        background: linear-gradient(90deg, #FF4B2B 0%, #FF416C 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 50px !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        border-radius: 50px !important;
        box-shadow: 0 10px 25px rgba(255, 75, 43, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        margin: 0 auto;
        display: block;
    }
    div.stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 15px 35px rgba(255, 75, 43, 0.6) !important;
    }

    /* Welcome Card สไตล์หรู */
    .welcome-card {
        background: #0f172a;
        padding: 80px 40px;
        border-radius: 40px;
        color: white;
        text-align: center;
        max-width: 850px;
        margin: 10vh auto 30px auto;
        box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6);
        border: 1px solid #1e293b;
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

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div style="background: white; padding: 15px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 25px;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: bold; letter-spacing: 0.05em;">SYSTEM ACTIVE</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: #1e293b; margin-top: 5px;">{now.strftime("%d %b %Y")}</div>
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

# --- 5. MAIN CONTENT (Welcome Screen) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div class="welcome-card">
            <div style="font-size: 5rem; margin-bottom: 20px;">📈</div>
            <h1 style="font-size: 3.8rem; font-weight: 800; letter-spacing: -2px; margin-bottom: 10px;">Sales Monitoring</h1>
            <div style="width: 60px; height: 5px; background: #38bdf8; margin: 25px auto; border-radius: 10px;"></div>
            <p style="font-size: 1.3rem; color: #94a3b8; margin-bottom: 40px; line-height: 1.6;">
                Enterprise Performance Tracking System<br>
                <span style="font-size: 1rem; opacity: 0.8;">กรุณากดปุ่มด้านล่างเพื่อเปิดเมนูจัดการข้อมูล</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ปุ่มเปิด Sidebar แบบบังคับ Re-render
    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        if st.button("📂 OPEN CONTROL PANEL"):
            st.query_params["nav"] = "open"
            st.rerun()
            
    # ถ้า Sidebar กางแล้ว ให้แสดงคำแนะนำ
    if st.query_params["nav"] == "open":
        st.markdown("""
            <div style="text-align: center; color: #3a7bd5; font-weight: bold; margin-top: 20px; animation: bounce 2s infinite;">
                👈 เลือกแบรนด์ที่เมนูด้านซ้ายได้เลยครับ
            </div>
            <style>
            @keyframes bounce { 0%, 20%, 50%, 80%, 100% {transform: translateX(0);} 40% {transform: translateX(-10px);} 60% {transform: translateX(-5px);} }
            </style>
        """, unsafe_allow_html=True)
        
    st.stop()

# --- 6. DASHBOARD VIEW (เมื่อเลือกแบรนด์แล้ว) ---
# เมื่อเลือกแบรนด์แล้ว ให้ล้าง Query Param เพื่อความสะอาด
if st.query_params.get("nav") == "open":
    st.query_params["nav"] = "done"

st.title(f"📈 {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            query = st_keyup("🔍 ค้นหาสาขา...", key=f"f_{selected_brand}").strip().lower()
            
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
            
            if st.button("💾 บันทึกการตั้งค่า", use_container_width=True, type="primary"):
                all_configs[selected_brand] = {s: st.session_state.get(f"tg_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    # ตาราง Heatmap
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
    st.warning("ไม่พบข้อมูลแบรนด์นี้")
