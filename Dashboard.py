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
    /* 1. ฆ่า Cursor กระพริบในทุกระดับชั้น (รวมถึง st-keyup) */
    * { caret-color: transparent !important; }
    input, textarea, [contenteditable] { caret-color: transparent !important; }
    
    /* 2. ซ่อน Header/Footer มาตรฐาน */
    header, footer { visibility: hidden !important; }

    /* 3. ปรับแต่ง Sidebar ให้ดูหรู (Modern Slate) */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 4px 0 10px rgba(0,0,0,0.02) !important;
    }
    
    /* กล่องวันที่สไตล์ Dashboard มืออาชีพ */
    .sb-date-container {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 25px;
    }

    /* 4. หน้า Welcome แบบ Modern Card */
    .welcome-card-outer {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
        pointer-events: none; /* ป้องกันไม่ให้บังการคลิก Sidebar */
    }
    .welcome-card-inner {
        background: #0f172a;
        padding: 50px 80px;
        border-radius: 32px;
        color: white;
        text-align: center;
        max-width: 750px;
        pointer-events: auto; /* ให้คลิกใน card ได้ปกติ */
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
        border: 1px solid #1e293b;
    }
    .title-text { font-size: 3.8rem; font-weight: 800; letter-spacing: -2px; margin: 10px 0; }
    .sub-title-text { font-size: 1.15rem; color: #94a3b8; font-weight: 300; line-height: 1.6; }
    .accent-line { width: 45px; height: 4px; background: #38bdf8; margin: 25px auto; border-radius: 10px; }
    
    /* ปรับแต่งปุ่มและ Expander ใน Sidebar */
    .stButton > button { border-radius: 10px !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA UTILITIES ---
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

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="sb-date-container">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 5px;">CURRENT STATUS</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #1e293b;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Configuration")
    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Monitoring Brand", brand_list, index=0)
    
    col1, col2 = st.columns(2)
    with col1: target_y = st.selectbox("Year", [2025, 2026], index=1)
    with col2:
        m_names = list(calendar.month_name)[1:]
        m_target_name = st.selectbox("Month", m_names, index=now.month-1)
        target_m = m_names.index(m_target_name) + 1

    summary_st = st.empty()
    st.markdown("---")

# --- 4. DISPLAY LOGIC ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div class="welcome-card-outer">
            <div class="welcome-card-inner">
                <div style="font-size: 4.5rem; margin-bottom: 10px;">📈</div>
                <h1 class="title-text">Sales Monitoring</h1>
                <div class="accent-line"></div>
                <p class="sub-title-text">
                    Ready to track performance? Please select a brand from the<br>
                    <b>Control Panel</b> on the left to load enterprise data.
                </p>
                <div style="margin-top: 35px; font-size: 0.85rem; color: #475569;">
                    System Status: <span style="color: #10b981; font-weight: bold;">● Active</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW ---
st.markdown(f"### 📈 Dashboard : {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 Branch Visibility Control", expanded=False):
            # ค้นหาสาขา (st-keyup จะไม่มี cursor กวนใจแล้ว)
            query = st_keyup("🔍 Filter branches...", key=f"f_{selected_brand}").strip().lower()
            
            # Master Toggle Logic
            m_key = f"m_toggle_{selected_brand}"
            def sync_all():
                for s in unique_shops: st.session_state[f"toggle_{selected_brand}_{s}"] = st.session_state[m_key]
            
            is_all_active = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("Toggle All Branches", value=is_all_active, key=m_key, on_change=sync_all)
            st.markdown("---")
            
            new_settings = {}
            for shop in unique_shops:
                if query and query not in shop.lower(): continue
                t_key = f"toggle_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                new_settings[shop] = st.toggle(shop, key=t_key)
            
            if st.button("💾 Apply Configuration", type="primary", use_container_width=True):
                all_configs[selected_brand] = {s: st.session_state.get(f"toggle_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("Config Updated!")
                st.rerun()

    # Heatmap Processing
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
                code = row['status_code']
                heatmap_grid.at[row['shop_name'], row['Day']] = "✅" if code == 2 else "⚠️" if code == 1 else "❌"

    # Sidebar Summary
    active_count = sum(current_settings.get(s, True) for s in unique_shops)
    with summary_st.container():
        st.info(f"Monitoring: **{active_count}** Branches")

    # Heatmap Styling
    def style_cells(val):
        if val == "✅": return 'background-color: #dcfce7; color: #166534;'
        if val == "⚠️": return 'background-color: #fef9c3; color: #854d0e;'
        if val == "❌": return 'background-color: #fee2e2; color: #991b1b;'
        if val == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #cbd5e1;'

    st.dataframe(heatmap_grid.style.map(style_cells), use_container_width=True, height=750)
else:
    st.warning("No data found for this selection.")
