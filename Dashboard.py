import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SET CONFIG (บังคับกาง Sidebar) ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS NEW GENERATION (ล้างชื่อ Class เดิมทิ้งทั้งหมด) ---
st.markdown("""
    <style>
    /* ซ่อน Cursor กระพริบทั้งระบบ */
    * { caret-color: transparent !important; }
    
    /* ซ่อน Header/Footer ของ Streamlit */
    header, footer { visibility: hidden !important; }

    /* ปรับแต่ง Sidebar ให้เด่นและกดได้ 100% */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        z-index: 1000001 !important; /* ดันขึ้นมาบนสุด */
    }

    /* กล่องวันที่ใน Sidebar */
    .sidebar-date-box {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #cbd5e1;
        text-align: center;
        margin-bottom: 20px;
    }

    /* หน้า Welcome แบบ Card (ไม่ใช้ vh เต็มจอเพื่อไม่ให้ทับปุ่ม) */
    .main-welcome-area {
        margin: 5% auto;
        padding: 50px;
        background: #0f172a; /* สีกรมท่าเข้มแบบโปร */
        border-radius: 24px;
        color: white;
        text-align: center;
        max-width: 900px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .welcome-title { font-size: 3.5rem; font-weight: 800; margin-bottom: 10px; }
    .welcome-sub { font-size: 1.2rem; color: #94a3b8; }
    .status-line { width: 60px; height: 4px; background: #38bdf8; margin: 20px auto; }
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
        <div class="sidebar-date-box">
            <div style="font-size: 0.8rem; color: #64748b; font-weight: bold;">SYSTEM READY</div>
            <div style="font-size: 1.1rem; color: #1e293b; font-weight: bold; margin-top: 5px;">
                {now.strftime("%A, %d %b %Y")}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Enterprise Settings")
    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Select Target Brand", brand_list, index=0)
    
    c1, c2 = st.columns(2)
    with c1: year = st.selectbox("Year", [2025, 2026], index=1)
    with c2:
        m_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("Month", m_list, index=now.month-1)
        month = m_list.index(m_name) + 1

    summary_st = st.empty()
    st.markdown("---")

# --- 5. MAIN CONTENT LOGIC ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # หน้า Welcome ที่เปลี่ยนชื่อ Class และโครงสร้างใหม่หมดเพื่อแก้ปัญหา Sidebar หาย
    st.markdown("""
        <div class="main-welcome-area">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h1 class="welcome-title">Sales Monitoring</h1>
            <div class="status-line"></div>
            <p class="welcome-sub">
                To start, please select a brand from the <b>sidebar menu on the left</b>.
            </p>
            <div style="margin-top: 30px; font-size: 0.9rem; color: #475569;">
                System Status: <span style="color: #22c55e;">● Online</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD (เมื่อเลือกแบรนด์แล้ว) ---
st.header(f"📈 Dashboard: {selected_brand}")
df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not df.empty:
    shops = sorted(df['shop_name'].unique())
    config = get_config()
    settings = config.get(selected_brand, {})

    # จัดการสาขาใน Sidebar
    with st.sidebar:
        with st.expander("🚫 Visibility Control", expanded=False):
            search = st_keyup("🔍 Filter branch...", key=f"filter_{selected_brand}").strip().lower()
            
            master_key = f"master_tg_{selected_brand}"
            def toggle_all():
                for s in shops: st.session_state[f"st_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(settings.get(s, True) for s in shops)
            st.toggle("Toggle All Branches", value=all_on, key=master_key, on_change=toggle_all)
            
            new_settings = {}
            for s in shops:
                if search and search not in s.lower(): continue
                t_key = f"st_{selected_brand}_{s}"
                if t_key not in st.session_state: st.session_state[t_key] = settings.get(s, True)
                new_settings[s] = st.toggle(s, key=t_key)
            
            if st.button("Save Configuration", type="primary", use_container_width=True):
                config[selected_brand] = {s: st.session_state.get(f"st_{selected_brand}_{s}", True) for s in shops}
                save_config(config)
                st.success("Config Saved!")
                st.rerun()

    # ทำตาราง
    mask = (df['sync_date'].dt.month == month) & (df['sync_date'].dt.year == year)
    df_f = df[mask].copy()
    _, last_day = calendar.monthrange(year, month)
    grid = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_f.empty:
        df_f['Day'] = df_f['sync_date'].dt.day
        for s in shops:
            if not settings.get(s, True): grid.loc[s] = "DISABLED"
        for _, r in df_f.iterrows():
            if r['shop_name'] in grid.index and grid.at[r['shop_name'], r['Day']] != "DISABLED":
                stc = r['status_code']
                grid.at[r['shop_name'], r['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    def grid_style(v):
        if v == "✅": return 'background-color: #dcfce7; color: #166534;'
        if v == "⚠️": return 'background-color: #fef9c3; color: #854d0e;'
        if v == "❌": return 'background-color: #fee2e2; color: #991b1b;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #e2e8f0;'

    st.dataframe(grid.style.map(grid_style), use_container_width=True, height=750)
else:
    st.warning("No data available.")
