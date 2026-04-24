import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SESSION STATE (ต้องอยู่บนสุดเพื่อคุม Sidebar) ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS (เน้นให้ปุ่มอยู่กลาง และสีพื้นหลังเต็มหน้า) ---
st.markdown("""
    <style>
    /* พื้นหลังหน้า Welcome */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    /* ถ้าเลือกแบรนด์แล้ว ให้พื้นหลังกลับมาปกติ */
    .app-selected {
        background: white !important;
    }
    
    /* ตกแต่งปุ่ม GET STARTED */
    div.stButton > button {
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        font-weight: bold !important;
        padding: 20px 40px !important;
        font-size: 1.5rem !important;
        border-radius: 50px !important;
        border: none !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        width: 100% !important;
    }
    
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
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

# --- 4. SIDEBAR (สร้างรอไว้เลย กัน Error) ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"### 📅 {now.strftime('%d %b %Y')}")
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. WELCOME PAGE (ทำให้ปุ่มกดติดชัวร์) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # สร้างพื้นที่ว่างให้ปุ่มลงมาอยู่กลางจอ
    for _ in range(8): st.write("") 
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; color:white; font-size:4rem;'>📊</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; color:white;'>Sales Monitoring</h1>", unsafe_allow_html=True)
        st.write("")
        
        # ปุ่ม Get Started ของจริง (ไม่ใช้ HTML มาบัง เพื่อให้คลิกติด 100%)
        if st.button("🚀 GET STARTED"):
            st.session_state.sidebar_state = 'expanded'
            st.rerun()
            
    st.stop()

#
