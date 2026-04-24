import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime

# --- 1. CONFIG: บังคับกาง Sidebar และตั้งค่าหน้าจอ ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS: ปรับให้เนียน ไม่ต้องใช้ Markdown เยอะเพื่อลดอาการ Cursor กะพริบ ---
st.markdown("""
    <style>
    /* ปรับแต่งตารางให้ดูสะอาด */
    [data-testid="stTable"] { font-size: 14px; }
    /* ปรับแต่ง Sidebar */
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    /* ปรับแต่ง Metric */
    .stMetric { border: 1px solid #eee; padding: 10px; border-radius: 8px; background: white; }
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

@st.cache_data(ttl=60) # เพิ่มเวลา Cache นิดนึงเพื่อความนิ่ง
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
    st.title("📊 Sales Monitor")
    now = datetime.now()
    st.info(f"📅 วันนี้: {now.strftime('%d %b %Y')}")
    
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_options, index=0)
    
    st.markdown("---")
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    sidebar_summary = st.empty()

# --- 5. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.write("##")
    st.markdown("<h2 style='text-align: center; color: #6c757d;'>👈 กรุณาเลือกแบรนด์ที่เมนูซ้ายมือ</h2>", unsafe_allow_html=True)
else:
    st.subheader(f"📈 Dashboard: {selected_brand}")
    full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

    if not full_df.empty:
        # ดึง Config การเปิด/ปิดสาขา (ไม่ Cache เพื่อให้ Update Realtime)
        try:
            brand_settings = requests.get(CONFIG_API, timeout=5).json().get(selected_brand, {})
        except:
            brand_settings = {}
            
        shops = sorted(full_df['shop_name'].unique())
        
        # เตรียมตาราง Heatmap
        mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
        df_filtered = full_df[mask].copy()
        _, last_day = calendar.monthrange(y, m)
        days = list(range(1, last_day + 1))
        grid_df = pd.DataFrame("N/A", index=shops, columns=days)

        if not df_filtered.empty:
            df_filtered['Day'] = df_filtered['sync_date'].dt.day
            for shop in shops:
                if not brand_settings.get(shop, True): 
                    grid_df.loc[shop] = "DISABLED"
            
            for _, row in df_filtered.iterrows():
                sn, dy, sc = row['shop_name'], row['Day'], row['status_code']
                if sn in grid_df.index and grid_df.at[sn, dy] != "DISABLED":
                    grid_df.at[sn, dy] = "✅" if sc == 2 else "⚠️" if sc == 1 else "❌"
        
        # สรุปผลลง Sidebar
        with sidebar_summary.container():
            active_list = [s for s in shops if brand_settings.get(s, True)]
            st.metric("สาขาที่เปิดใช้งาน", f"{len(active_list)} / {len(shops)}")

        # ฟังก์ชันระบายสี (ใช้แบบง่ายๆ เพื่อประสิทธิภาพ)
        def apply_style(val):
            if val == "✅": return 'background-color: #d4edda;'
            if val == "⚠️": return 'background-color: #fff3cd;'
            if val == "❌": return 'background-color: #f8d7da;'
            if val == "DISABLED": return 'background-color: #f1f3f5; color: #ced4da;'
            return 'color: #f8f9fa;'

        # แสดงผลตาราง (ใช้ applymap แบบดั้งเดิมที่เสถียรกว่า)
        st.dataframe(
            grid_df.style.applymap(apply_style), 
            use_container_width=True, 
            height=700
        )
    else:
        st.warning("⚠️ ไม่พบข้อมูลสำหรับเดือน/ปี ที่เลือก")
