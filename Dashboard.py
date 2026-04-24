import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & SESSION STATE ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CSS (เน้นแค่ความสวยงาม ไม่ขวางปุ่ม) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f2027;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    .welcome-text {
        text-align: center;
        color: white;
        font-family: 'sans-serif';
    }
    div.stButton > button {
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        font-weight: bold !important;
        padding: 15px 50px !important;
        font-size: 1.2rem !important;
        border-radius: 30px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3) !important;
    }
    /* แก้ไข Sidebar ให้ดูดี */
    [data-testid="stSidebar"] { background-color: #ffffff !important; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONFIG ---
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

# --- 4. SIDEBAR (ใส่ไว้ตอนแรกเพื่อกัน NameError) ---
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
    
    sidebar_summary = st.empty() # ตัวนี้แหละที่กัน Error

# --- 5. WELCOME PAGE (จัดกลางด้วย Columns) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # สร้างช่องว่าง บน-ล่าง เพื่อให้คอนเทนต์อยู่กลางจอ
    st.write("##")
    st.write("##")
    st.write("##")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="welcome-text">
                <h1 style='font-size: 5rem;'>📊</h1>
                <h1 style='font-size: 3rem;'>Sales Monitoring</h1>
                <p style='opacity: 0.8;'>Enterprise Dashboard System</p>
            </div>
        """, unsafe_allow_html=True)
        
        # ปุ่ม Get Started ของจริง กดติด 100%
        if st.button("🚀 GET STARTED"):
            st.session_state.sidebar_state = 'expanded'
            st.rerun()
            
    st.stop()

# --- 6. DASHBOARD (จะแสดงเมื่อเลือกแบรนด์) ---
# เคลียร์พื้นหลังให้กลับมาเป็นสีปกติ
st.markdown("<style>.stApp { background: white !important; }</style>", unsafe_allow_html=True)

st.title(f"📊 {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    current_full_config = requests.get(CONFIG_API).json()
    brand_settings = current_full_config.get(selected_brand, {})
    shops = sorted(full_df['shop_name'].unique())

    # Heatmap Logic
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
            if row['shop_name'] in grid_df.index and grid_df.at[row['shop_name'], row['Day']] != "DISABLED":
                stc = row['status_code']
                grid_df.at[row['shop_name'], row['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌" if stc == 0 else "N/A"

    # แสดงผล Summary ใน Sidebar (เรียกใช้ผ่าน Placeholder)
    with sidebar_summary.container():
        active_cnt = len([s for s in shops if brand_settings.get(s, True)])
        st.metric("สาขาที่เปิด Monitor", f"{active_cnt} / {len(shops)}")

    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda;'
        if val == "⚠️": return 'background-color: #fff3cd;'
        if val == "❌": return 'background-color: #f8d7da;'
        if val == "DISABLED": return 'background-color: #eeeeee; color: #cccccc;'
        return 'color: #eeeeee;'

    st.dataframe(grid_df.style.applymap(apply_style), use_container_width=True, height=700)
else:
    st.warning("ไม่มีข้อมูล")
