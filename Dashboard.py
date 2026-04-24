import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & URL HANDLING (ไม้ตายเรื่องการกดปุ่ม) ---
# ตรวจสอบว่ามีการกดปุ่ม Get Started ผ่าน URL หรือไม่
query_params = st.query_params
if query_params.get("action") == "get_started":
    st.session_state.sidebar_state = 'expanded'
    # ล้าง parameter ทิ้งเพื่อให้หน้าจอยังทำงานปกติ
    st.query_params.clear()

if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS (ระเบิดขอบ และจัดกลางจอแบบ Absolute) ---
st.markdown("""
    <style>
    /* ซ่อน Header มาตรฐานของ Streamlit */
    header {visibility: hidden;}
    [data-testid="stAppViewBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
    
    .full-bg {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        height: 100vh;
        width: 100vw;
        display: flex;
        justify-content: center;
        align-items: center;
        position: fixed;
        top: 0; left: 0;
        z-index: 1000;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 60px;
        border-radius: 40px;
        text-align: center;
        box-shadow: 0 40px 80px rgba(0,0,0,0.5);
        width: 500px;
    }

    .btn-get-started {
        display: inline-block;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        color: white !important;
        text-decoration: none !important;
        padding: 18px 50px;
        font-size: 1.5rem;
        font-weight: 800;
        border-radius: 50px;
        margin-top: 30px;
        transition: 0.3s;
        box-shadow: 0 10px 30px rgba(79, 172, 254, 0.5);
        border: none;
        cursor: pointer;
    }
    
    .btn-get-started:hover {
        transform: scale(1.05);
        box-shadow: 0 15px 40px rgba(79, 172, 254, 0.7);
    }
    
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONFIG ---
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

# --- 4. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""<div style='text-align:center; padding:10px; background:#f0f2f6; border-radius:10px;'>
                 <b>📅 Today: {now.strftime('%d %b %Y')}</b></div>""", unsafe_allow_html=True)
    
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. WELCOME PAGE (จัดกลางจอแบบเป๊ะ 100%) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown(f"""
        <div class="full-bg">
            <div class="glass-card">
                <div style="font-size: 5rem; margin-bottom: 10px;">📊</div>
                <h1 style="color: white; font-size: 3rem; font-weight: 800; margin: 0;">Sales Monitoring</h1>
                <p style="color: #bdc3c7; font-size: 1.1rem; margin-top: 10px;">Enterprise Intelligence Dashboard</p>
                <a href="/?action=get_started" target="_self" class="btn-get-started">🚀 GET STARTED</a>
                <p style="color: rgba(255,255,255,0.3); font-size: 0.8rem; margin-top: 30px;">
                    Click to open control panel
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 6. MAIN CONTENT (เมื่อเลือกแบรนด์แล้ว) ---
# คืนค่า Padding ให้หน้า Dashboard ปกติ
st.markdown("<style>[data-testid='stAppViewBlockContainer'] { padding: 2rem !important; } header {visibility: visible;}</style>", unsafe_allow_html=True)

st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหา...", key=f"src_{selected_brand}").strip().lower()
            master_key = f"master_{selected_brand}"
            def on_master_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 ทั้งหมด", value=all_on, key=master_key, on_change=on_master_change)
            
            updated_settings = {}
            for shop in shops:
                if search_query and search_query not in shop.lower(): continue
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            if st.button("💾 บันทึก", use_container_width=True, type="primary"):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("Saved!")
                st.rerun()

    # Heatmap Setup
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
            sn, dy, st_c = row['shop_name'], row['Day'], row['status_code']
            if sn in grid_df.index and grid_df.at[sn, dy] != "DISABLED":
                grid_df.at[sn, dy] = "✅" if st_c == 2 else "⚠️" if st_c == 1 else "❌" if st_c == 0 else "N/A"

    with sidebar_summary.container():
        active_list = [s for s in shops if brand_settings.get(s, True)]
        st.write(f"Active Shops: **{len(active_list)}**")
        if active_list:
            active_grid = grid_df.loc[active_list]
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            st.metric("Found Problems", prob_count)

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ No data found.")
