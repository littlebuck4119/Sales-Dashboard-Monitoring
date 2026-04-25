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
    /* 1. ซ่อน Cursor กระพริบทั่วทั้งแอป */
    * { caret-color: transparent !important; }
    
    /* 2. ซ่อน Header/Footer และเปิดทางให้ Sidebar */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 3. บังคับให้ปุ่มเปิด Sidebar ลอยเด่น ไม่โดนทับ */
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 9999999 !important;
        background-color: rgba(255,255,255,0.5);
        border-radius: 50%;
    }

    /* 4. สไตล์ Sidebar Professional */
    [data-testid="stSidebarContent"] { 
        padding-top: 1rem !important; 
        background-color: #f8f9fa;
    }
    .date-card { 
        background-color: #ffffff; padding: 15px; border-radius: 12px; 
        border: 1px solid #e0e0e0; text-align: center; margin-bottom: 20px;
    }
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
        <div class="date-card">
            <div style="font-size: 0.8rem; color: #666;">Current Date</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Control Panel")
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Select Brand", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("Year", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("Month", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()
    st.markdown("---")

# --- 4. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        /* แก้ไขการแสดงผลเพื่อไม่ให้ทับ Sidebar Control */
        [data-testid="stAppViewBlockContainer"] { 
            padding: 0 !important; 
            max-width: 100% !important; 
        }
        .welcome-bg {
            background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #f1f5f9;
            text-align: center;
        }
        .main-title { font-size: 4.5rem; font-weight: 800; letter-spacing: -2px; margin: 0; color: #ffffff; }
        .sub-text { font-size: 1.4rem; color: #94a3b8; margin-top: 15px; }
        .accent-bar { width: 60px; height: 4px; background: #38bdf8; margin: 20px 0; border-radius: 2px; }
        </style>
        <div class="welcome-bg">
            <h1 class="main-title">Sales Monitoring</h1>
            <div class="accent-bar"></div>
            <p class="sub-text">Please select a brand on the <b>sidebar</b> to view data.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW ---
st.markdown(f"### 📈 {selected_brand} Dashboard")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 Manage Branch Visibility", expanded=False):
            search_query = st_keyup("🔍 Search branch...", key=f"search_{selected_brand}").strip().lower()
            
            m_key = f"master_{selected_brand}"
            def on_master_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("Toggle All Branches", value=all_on, key=master_key, on_change=on_master_change)
            
            updated_settings = {}
            for shop in shops:
                if search_query and search_query not in shop.lower(): continue
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            if st.button("💾 Save Settings", type="primary"):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("Success!")
                st.rerun()

    # Table Processing
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid_df = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for s in shops:
            if not brand_settings.get(s, True): grid_df.loc[s] = "DISABLED"
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index and grid_df.at[row['shop_name'], row['Day']] != "DISABLED":
                stc = row['status_code']
                grid_df.at[row['shop_name'], row['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    with summary_placeholder.container():
        active_list = [s for s in shops if brand_settings.get(s, True)]
        st.info(f"Active: **{len(active_list)}** / {len(shops)} branches")

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #e2e8f0;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=750)
else:
    st.warning("No data found.")
