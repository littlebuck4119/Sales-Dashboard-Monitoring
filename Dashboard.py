import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & STYLES ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 1.2rem !important; }
    /* ปรับ Padding ปกติสำหรับหน้า Dashboard */
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-bottom: 0rem !important; }
    
    button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
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

# --- 4. MAIN CONTENT (หน้า Welcome - ปรับสีอ่อนลงและชิดขอบบน) ---

if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        /* บังคับให้หน้า Welcome ชิดขอบบนสุด */
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 0 !important;
            max-width: 100% !important;
        }
        
        .full-screen-welcome {
            /* เปลี่ยนสีพื้นหลังให้อ่อนลง เป็นโทนฟ้า-เทาสว่าง */
            background: linear-gradient(135deg, #eef2f3 0%, #8e9eab 100%);
            height: 100vh;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #2c3e50; /* เปลี่ยนสีตัวอักษรให้เข้มขึ้นเพื่อให้เข้ากับพื้นหลังอ่อน */
            text-align: center;
            margin: 0;
            font-family: 'Inter', sans-serif;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.4); /* ขาวโปร่งแสง */
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.6);
            padding: 60px;
            border-radius: 40px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.05);
            max-width: 700px;
        }

        .main-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: -2px;
            margin-bottom: 10px;
            color: #34495e;
        }
        </style>
        
        <div class="full-screen-welcome">
            <div class="glass-card">
                <div style="font-size: 5rem; margin-bottom: 20px;">📊</div>
                <h1 class="main-title">Sales Monitoring</h1>
                <p style="font-size: 1.2rem; color: #576574; margin-bottom: 20px;">
                    Enterprise Performance Tracking Intelligence
                </p>
                <div style="height: 3px; width: 50px; background: #34495e; margin: 20px auto; border-radius: 10px;"></div>
                <p style="font-size: 1rem; color: #576574; opacity: 0.8;">
                    Please select a brand from the sidebar menu to get started.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW (ส่วนเดิมไม่เปลี่ยนแปลง Layout) ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    # ... (ส่วนประมวลผลข้อมูลคงเดิมตามไฟล์ Dashboard (2).py) ...
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"ks_{selected_brand}").strip().lower()
            master_key = f"ms_{selected_brand}"
            def on_master():
                for s in shops: st.session_state[f"t_{selected_brand}_{s}"] = st.session_state[master_key]
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 **เปิด/ปิด ทั้งหมด**", value=all_on, key=master_key, on_change=on_master)
            updated_settings = {s: st.session_state.get(f"t_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}
            filtered = [s for s in shops if search_query in s.lower()] if search_query else shops
            for shop in filtered:
                t_key = f"t_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid_df = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in shops:
            if not brand_settings.get(shop, True): grid_df.loc[shop] = "DISABLED"
        for _, row in df_filtered.iterrows():
            s, d, st_c = row['shop_name'], row['Day'], row['status_code']
            if s in grid_df.index and grid_df.at[s, d] != "DISABLED":
                grid_df.at[s, d] = "✅" if st_c == 2 else "⚠️" if st_c == 1 else "❌"

    # สรุปผล
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    with summary_placeholder.container():
        st.info(f"Monitor: **{len(active_shops)}** สาขา")
        if not active_grid.empty:
            prob_rows = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            c1, c2 = st.columns(2)
            c1.metric("ปกติ ✅", len(active_shops) - prob_rows)
            c2.metric("ปัญหา ⚠️", prob_rows)

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")
