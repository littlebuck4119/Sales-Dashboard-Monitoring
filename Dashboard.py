import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. INITIAL SESSION STATE ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

# --- 2. CONFIG ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 3. CSS (รวมทุกอย่างไว้ที่เดียว) ---
st.markdown("""
    <style>
    /* ระเบิดขอบเต็มจอสำหรับหน้า Welcome */
    .stAppHeader { background: transparent !important; }
    [data-testid="stSidebarContent"] { padding-top: 1rem !important; }
    
    /* แก้ไขการแสดงผล Dashboard ปกติ */
    .dashboard-container { padding: 2rem; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }

    /* ปรับแต่งปุ่ม Get Started ให้เด่นกลางจอ */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 40px !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        box-shadow: 0 10px 25px rgba(79, 172, 254, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA & CONFIG LOGIC ---
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
def get_data_from_api(url):
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

current_full_config = get_config()

# --- 5. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.info(f"📅 Today: **{now.strftime('%d %b %Y')}**")
    
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    # สร้าง Placeholder ไว้ใน Sidebar เลยเพื่อกัน NameError
    sidebar_summary = st.empty()

# --- 6. WELCOME PAGE (Full Screen & Centralized) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); 
                    height: 100vh; display: flex; align-items: center; justify-content: center; margin: -100px -50px;">
            <div style="background: rgba(255,255,255,0.05); padding: 80px; border-radius: 40px; 
                        text-align: center; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(20px); width: 600px;">
                <h1 style="font-size: 5rem; margin: 0;">📊</h1>
                <h1 style="color: white; font-size: 3rem; font-weight: 800; margin-bottom: 10px;">Sales Monitoring</h1>
                <p style="color: #bdc3c7; font-size: 1.2rem; margin-bottom: 40px;">Please open control panel to continue</p>
    """, unsafe_allow_html=True)
    
    # ปุ่มอยู่ตรงนี้ กึ่งกลาง Card แน่นอน
    if st.button("🚀 GET STARTED"):
        st.session_state.sidebar_state = 'expanded'
        st.rerun()
        
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN DASHBOARD CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหา...", key=f"search_{selected_brand}").strip().lower()
            master_key = f"master_{selected_brand}"
            def on_master_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 เปิด/ปิด ทั้งหมด", value=all_on, key=master_key, on_change=on_master_change)
            
            updated_settings = {}
            for shop in shops:
                if search_query and search_query not in shop.lower(): continue
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            if st.button("💾 บันทึก", use_container_width=True):
                current_full_config[selected_brand] = {s: st.session_state.get(f"tog_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}
                save_config(current_full_config)
                st.success("Saved!")
                st.rerun()

    # Heatmap Logic
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
            s_name, d, status = row['shop_name'], row['Day'], row['status_code']
            if s_name in grid_df.index and grid_df.at[s_name, d] != "DISABLED":
                grid_df.at[s_name, d] = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"

    # Sidebar Summary (ใช้ชื่อตัวแปรที่ประกาศไว้ข้างบน กัน NameError)
    with sidebar_summary.container():
        active_shops = [s for s in shops if brand_settings.get(s, True)]
        st.write(f"Active: **{len(active_shops)}** / **{len(shops)}**")
        if active_shops:
            active_grid = grid_df.loc[active_shops]
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            st.metric("ปัญหา ⚠️/❌", prob_count)
            prob_sum = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
            for shop, count in top_prob.items():
                st.markdown(f'<div class="problem-item"><b>{shop}</b> ({int(count)})</div>', unsafe_allow_html=True)

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ No data found.")
