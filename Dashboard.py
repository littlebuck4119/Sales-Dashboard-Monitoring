import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SUPER CONFIG (ตัวคุม Sidebar ของจริง) ---
# เช็คจาก URL ตรงๆ เลยว่ามีการกดปุ่มมาไหม
if st.query_params.get("nav") == "open":
    st.session_state.sidebar_state = "expanded"

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS (เน้นสะอาด ไม่ขวางปุ่ม) ---
st.markdown("""
    <style>
    .welcome-container {
        text-align: center;
        padding-top: 10vh;
        color: white;
    }
    /* ปรับปุ่มให้ใหญ่และอยู่กลาง */
    div.stButton > button {
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        font-weight: bold !important;
        padding: 25px 60px !important;
        font-size: 1.8rem !important;
        border-radius: 60px !important;
        border: none !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
        transition: 0.3s;
    }
    div.stButton > button:hover { transform: scale(1.05); }
    
    /* ฉากหลังหน้าแรก */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA API ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

@st.cache_data(ttl=30)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
            df['sync_date'] = pd.to_datetime(df['sync_date'])
            return df
    except: return pd.DataFrame()

# --- 4. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.title("⚙️ Control Panel")
    st.info(f"Today: {now.strftime('%d %b %Y')}")
    
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. WELCOME PAGE (CENTERED & FUNCTIONAL) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 6rem;'>📊</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 3.5rem;'>Sales Monitoring</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2rem; opacity: 0.7;'>Enterprise Intelligence System</p>", unsafe_allow_html=True)
    st.write("##")
    
    # จัดปุ่มไว้ตรงกลางด้วย Columns
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        if st.button("🚀 GET STARTED", use_container_width=True):
            # ยิง Query Param เพื่อบังคับให้ App Re-render และเปิด Sidebar
            st.query_params.update(nav="open")
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. MAIN DASHBOARD ---
st.markdown("<style>.stApp { background: white !important; color: black !important; }</style>", unsafe_allow_html=True)
st.title(f"📈 Dashboard: {selected_brand}")

full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    brand_settings = requests.get(CONFIG_API).json().get(selected_brand, {})
    shops = sorted(full_df['shop_name'].unique())
    
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
            sn, dy, sc = row['shop_name'], row['Day'], row['status_code']
            if sn in grid_df.index and grid_df.at[sn, dy] != "DISABLED":
                grid_df.at[sn, dy] = "✅" if sc == 2 else "⚠️" if sc == 1 else "❌"
    
    with sidebar_summary.container():
        st.success(f"Loaded {len(shops)} shops")

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda;'
        if val == "⚠️": return 'background-color: #fff3cd;'
        if val == "❌": return 'background-color: #f8d7da;'
        return 'color: #eeeeee;'

    st.dataframe(grid_df.style.applymap(apply_style), use_container_width=True, height=600)
