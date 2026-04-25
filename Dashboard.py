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
    /* ซ่อน Header และ Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* บังคับให้ Sidebar ลอยอยู่เหนือทุกอย่าง เพื่อให้กดได้เสมอ */
    [data-testid="stSidebar"] { 
        z-index: 999999 !important; 
        background-color: #f8f9fa;
    }

    /* การ์ดและสไตล์ย่อย */
    .date-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
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
    st.markdown(f'<div class="date-card"><b>📅 {now.strftime("%A, %d %b %Y")}</b></div>', unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    st.markdown("---")
    summary_placeholder = st.empty() 
    st.markdown("---")
    manage_placeholder = st.empty()  

# --- 4. MAIN CONTENT ---

if selected_brand == "🛑 SELECT BRAND 🛑":
    # แก้ไข CSS Welcome: เว้นที่ให้ Sidebar (margin-left) และเอา max-width ออก
    st.markdown("""
        <style>
        [data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
        .welcome-bg {
            background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #f1f5f9;
            text-align: center;
            font-family: 'Inter', sans-serif;
            /* ป้องกันการทับ Sidebar
