import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CORE CONFIG ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # บังคับให้เมนูซ้ายกางเสมอ
)

# --- 2. THEME & CURSOR KILLER ---
st.markdown("""
    <style>
    /* ซ่อน Cursor กระพริบทั้งหมด */
    * { caret-color: transparent !important; }
    
    /* ซ่อน Header/Footer */
    header, footer { visibility: hidden !important; }

    /* บังคับความชัดเจนของ Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
        min-width: 320px !important;
    }
    
    /* ปรับแต่งช่องวันที่ให้ดูโปร */
    .date-card {
        background: white;
        padding: 1.2rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* หน้า Welcome Card สไตล์ Enterprise */
    .welcome-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    .welcome-card {
        background: #0f172a;
        padding: 4rem;
        border-radius: 30px;
        color: white;
        text-align: center;
        max-width: 800px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border: 1px solid #1e293b;
    }
    .main-title { font-size: 3.5rem; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 0.5rem; }
    .sub-text { font-size: 1.2rem; color: #94a3b8; font-weight: 300; }
    .blue-bar { width: 50px; height: 4px; background: #38bdf8; margin: 1.5rem auto; border-radius: 10px; }
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

# --- 4. SIDEBAR IMPLEMENTATION ---
with st.sidebar:
    # แสดงวันที่ปัจจุบันแบบสะอาดตา
    now = datetime.now()
    st.markdown(f"""
        <div class="date-card">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">SYSTEM DATE</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-top: 4px;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Brand Selection")
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Choose a brand to monitor", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("Year", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("Month", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()
    st.markdown("---")

# --- 5. PAGE LOGIC ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # หน้า Welcome ที่แก้ไขให้ไม่ทับ Sidebar
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-card">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📈</div>
                <h1 class="main-title">Sales Monitoring</h1>
                <div class="blue-bar"></div>
                <p class="sub-text">
                    Please select a brand from the <b>sidebar on the left</b><br>
                    to start tracking enterprise performance data.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD CONTENT ---
st.header(f"📊 {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    # จัดการสาขาใน Sidebar
    with st.sidebar:
        with st.expander("⚙️ Branch Visibility Settings", expanded=False):
            search = st_keyup("🔍 Search branch...", key=f"s_{selected_brand}").strip().lower()
            
            # Master Toggle
            m_key = f"m_{selected_brand}"
            def sync_toggles():
                for s in shops: st.session_state[f"t_{selected_brand}_{s}"] = st.session_state[m_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("Select/Deselect All", value=all_on, key=m_key, on_change=sync_toggles)
            st.markdown("---")
            
            new_config = {}
            for s in shops:
                if search and search not in s.lower(): continue
                t_key = f"t_{selected_brand}_{s}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(s, True)
                new_config[s] = st.toggle(s, key=t_key)
            
            if st.button("Apply & Save Settings", type="primary", use_container_width=True):
                current_full_config[selected_brand] = {s: st.session_state.get(f"t_{selected_brand}_{s}", True) for s in shops}
                save_config(current_full_config)
                st.success("Settings Updated!")
                st.rerun()

    # ประมวลผล Heatmap
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

    # สรุปข้อมูลใน Sidebar
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    with summary_placeholder.container():
        st.write(f"**Monitoring:** {len(active_shops)} / {len(shops)} Branches")

    # Styling Table
    def color_cells(v):
        if v == "✅": return 'background-color: #dcfce7; color: #166534;'
        if v == "⚠️": return 'background-color: #fef9c3; color: #854d0e;'
        if v == "❌": return 'background-color: #fee2e2; color: #991b1b;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #cbd5e1;'

    st.dataframe(grid.style.map(color_cells), use_container_width=True, height=750)
else:
    st.warning("No data found for the selected period.")
