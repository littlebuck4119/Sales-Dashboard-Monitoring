import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # บังคับกาง Sidebar
)

# --- 2. CSS ล็อค Sidebar + ซ่อน Cursor ---
st.markdown("""
    <style>
    /* ซ่อน Cursor กระพริบ */
    * { caret-color: transparent !important; }
    
    /* ปิด Header/Footer */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    /* ปรับแต่ง Sidebar ให้ดูแพง */
    [data-testid="stSidebarContent"] {
        background-color: #f1f5f9 !important;
    }
    
    /* การ์ดวันที่ */
    .date-box {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 20px;
    }

    /* หน้า Welcome แบบไม่ทับปุ่ม */
    .welcome-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 60px;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-top: 50px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA FETCHING ---
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

# --- 4. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="date-box">
            <div style="font-size: 0.8rem; color: #64748b;">CURRENT DATE</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: #1e293b;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Settings")
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Select Brand", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("Year", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("Month", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    st.markdown("---")
    summary_placeholder = st.empty()

# --- 5. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # หน้า Welcome แบบ Card (ไม่ทับจอ)
    st.markdown("""
        <div class="welcome-card">
            <div style="font-size: 50px;">📊</div>
            <h1 style="font-size: 3.5rem; font-weight: 800; margin: 10px 0;">Sales Monitoring</h1>
            <div style="width: 50px; height: 3px; background: #38bdf8; margin: 20px auto;"></div>
            <p style="font-size: 1.2rem; color: #94a3b8;">
                Please select a brand on the <b>left sidebar</b> to start monitoring.
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD (เมื่อเลือกแบรนด์) ---
st.header(f"📈 {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    # ตัวจัดการสาขาใน Sidebar
    with st.sidebar:
        with st.expander("🚫 Branch Settings", expanded=False):
            search = st_keyup("🔍 Search...", key=f"s_{selected_brand}").strip().lower()
            
            m_key = f"m_{selected_brand}"
            def sync():
                for s in shops: st.session_state[f"t_{selected_brand}_{s}"] = st.session_state[m_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("Toggle All", value=all_on, key=m_key, on_change=sync)
            
            new_set = {}
            for s in shops:
                if search and search not in s.lower(): continue
                t_key = f"t_{selected_brand}_{s}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(s, True)
                new_set[s] = st.toggle(s, key=t_key)
            
            if st.button("Save Settings", type="primary", use_container_width=True):
                current_full_config[selected_brand] = {s: st.session_state.get(f"t_{selected_brand}_{s}", True) for s in shops}
                save_config(current_full_config)
                st.success("Saved!")
                st.rerun()

    # ตาราง Heatmap
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_f = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_f.empty:
        df_f['Day'] = df_f['sync_date'].dt.day
        for s in shops:
            if not brand_settings.get(s, True): grid.loc[s] = "DISABLED"
        for _, r in df_f.iterrows():
            if r['shop_name'] in grid.index and grid.at[r['shop_name'], r['Day']] != "DISABLED":
                stc = r['status_code']
                grid.at[r['shop_name'], r['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    def style_table(v):
        if v == "✅": return 'background-color: #d4edda; color: #155724;'
        if v == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if v == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #e2e8f0;'

    st.dataframe(grid.style.map(style_table), use_container_width=True, height=700)
else:
    st.warning("No data found.")
