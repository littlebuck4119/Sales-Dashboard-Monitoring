import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SESSION STATE & CONFIG ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS: จัดกลางจอและทำให้ปุ่มกดง่าย ---
st.markdown("""
    <style>
    /* ระเบิดขอบเต็มจอ */
    [data-testid="stAppViewBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
    
    /* ฉากหลัง Welcome */
    .welcome-screen {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        height: 100vh;
        width: 100vw;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: fixed;
        top: 0; left: 0;
        z-index: 100;
        color: white;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 60px;
        border-radius: 40px;
        text-align: center;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        width: 80%;
        max-width: 600px;
    }

    /* ตกแต่งปุ่ม Streamlit ให้เป็นปุ่มใหญ่กลางหน้าจอ */
    div.stButton > button {
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        border: none !important;
        padding: 20px 60px !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        box-shadow: 0 10px 20px rgba(0, 242, 254, 0.3) !important;
        margin-top: 20px !important;
        transition: 0.3s !important;
        width: 100% !important;
    }
    div.stButton > button:hover { transform: scale(1.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA FETCHING (Logic เดิม) ---
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
            if not df.empty:
                df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
                df['sync_date'] = pd.to_datetime(df['sync_date'])
                return df
    except: pass
    return pd.DataFrame()

# --- 4. SIDEBAR (ใส่ไว้ก่อนเพื่อให้ทำงานได้ทุกที่) ---
with st.sidebar:
    now = datetime.now()
    st.write(f"📅 **{now.strftime('%A, %d %b %Y')}**")
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. WELCOME PAGE (Logic กดติดชัวร์) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # ใช้ Container ของ Streamlit เพื่อวางปุ่มให้ทำงานได้จริง
    with st.container():
        st.markdown('<div class="welcome-screen">', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h1 style="font-size: 5rem; margin-bottom: 0;">📊</h1>', unsafe_allow_html=True)
        st.markdown('<h1 style="color: white; font-size: 3rem; margin-bottom: 10px;">Sales Monitoring</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #bdc3c7; font-size: 1.2rem; margin-bottom: 30px;">Enterprise Intelligence Panel</p>', unsafe_allow_html=True)
        
        # ปุ่มจริงของ Streamlit ที่ถูกแต่งด้วย CSS ให้ดูพรีเมียม
        if st.button("🚀 GET STARTED", key="start_btn"):
            st.session_state.sidebar_state = 'expanded'
            st.rerun()
            
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# --- 6. MAIN DASHBOARD ---
# คืนค่า Padding ให้หน้า Dashboard
st.markdown("<style>[data-testid='stAppViewBlockContainer'] { padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.markdown(f"### 📊 Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = requests.get(CONFIG_API).json()
    brand_settings = current_full_config.get(selected_brand, {})

    # (Heatmap และ Logic สรุปผลเดิมของพี่ทั้งหมด...)
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
            sn, dy, stc = row['shop_name'], row['Day'], row['status_code']
            if sn in grid_df.index and grid_df.at[sn, dy] != "DISABLED":
                grid_df.at[sn, dy] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌" if stc == 0 else "N/A"

    with sidebar_summary.container():
        st.info(f"Active: {len([s for s in shops if brand_settings.get(s, True)])}")

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ No data found.")
