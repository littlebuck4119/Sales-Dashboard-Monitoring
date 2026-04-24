import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SESSION STATE & CONFIG (ต้องอยู่บนสุดและห้ามพลาด) ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS RESET & CUSTOM STYLES ---
st.markdown("""
    <style>
    /* ระเบิดขอบให้เต็มจอจริงๆ */
    [data-testid="stAppViewBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    
    /* ตกแต่ง Sidebar */
    .date-card { background-color: #ffffff; padding: 20px 15px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }

    /* หน้า Welcome แบบจัดกลางเป๊ะ */
    .welcome-wrapper {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        height: 100vh;
        width: 100vw;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 99;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 50px;
        border-radius: 40px;
        text-align: center;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA FETCHING (Logic เดิมของพี่) ---
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
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-top: 10px;">
            <div style="font-size: 0.8rem; color: #666;">📅 Today</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()

# --- 5. WELCOME PAGE (จัดกลางจอและปุ่มทำงานได้จริง) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # สร้าง Container เปล่าเพื่อใช้เป็นตัวครอบปุ่มให้ไปอยู่กลางจอ
    st.markdown('<div class="welcome-wrapper"><div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 4rem; margin:0;">📊</h1>', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 10px; color: white;">Sales Monitoring</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2rem; opacity: 0.8; color: white; margin-bottom: 30px;">Enterprise Performance Intelligence</p>', unsafe_allow_html=True)
    
    # วางปุ่ม Streamlit ไว้ตรงนี้ (มันจะถูกจัดกลางตาม CSS welcome-wrapper)
    if st.button("🚀 GET STARTED", type="primary"):
        st.session_state.sidebar_state = 'expanded'
        st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# --- 6. MAIN DASHBOARD (เมื่อเลือกแบรนด์แล้ว) ---
# คืนค่า Padding ให้หน้า Dashboard ปกติ
st.markdown("<style>[data-testid='stAppViewBlockContainer'] { padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"keyup_search_{selected_brand}").strip().lower()
            master_key = f"master_{selected_brand}"
            def on_master_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 **เปิด/ปิด ทั้งหมด**", value=all_on, key=master_key, on_change=on_master_change)
            
            updated_settings = {s: st.session_state.get(f"tog_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}
            filtered_shops = [s for s in shops if search_query in s.lower()] if search_query else shops

            for shop in filtered_shops:
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            if st.button("💾 บันทึกการตั้งค่า", use_container_width=True):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    # --- ตาราง Heatmap ---
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
            shop, day, status = row['shop_name'], row['Day'], row['status_code']
            if shop in grid_df.index and grid_df.at[shop, day] != "DISABLED":
                grid_df.at[shop, day] = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"

    # --- Summary ---
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    with summary_placeholder.container():
        st.info(f"Monitor: **{len(active_shops)}** / **{len(shops)}** สาขา")
        m1, m2 = st.columns(2)
        if active_shops:
            active_grid = grid_df.loc[active_shops]
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("ปกติ ✅", len(active_shops) - prob_count)
            m2.metric("ปัญหา ⚠️/❌", prob_count)

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")
