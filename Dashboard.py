import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. SESSION STATE ล็อคสถานะ ---
if "sidebar_active" not in st.session_state:
    st.session_state.sidebar_active = True # บังคับให้เปิดไว้ก่อนเลย

# --- 2. CONFIG แบบบ้านๆ ที่สุด ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.sidebar_active else "collapsed"
)

# --- 3. CSS เฉพาะซ่อน CURSOR เท่านั้น (ไม่ยุ่งกับ Layout อื่นแล้ว) ---
st.markdown("""
    <style>
    /* ซ่อน Cursor กระพริบ */
    * { caret-color: transparent !important; }
    
    /* ซ่อน Header/Footer */
    header, footer { visibility: hidden !important; }

    /* ทำให้ Sidebar มีสีต่างจากพื้นหลังนิดหน่อยให้ดูออก */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA UTILS ---
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
def fetch_api_data(url):
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

# --- 5. SIDEBAR (ใส่เนื้อหาแบบ Standard) ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    now = datetime.now()
    st.write(f"Current Date: **{now.strftime('%d %b %Y')}**")
    
    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_list, index=0)
    
    y = st.selectbox("ปี", [2025, 2026], index=1)
    m_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน", m_names, index=now.month-1)
    m = m_names.index(m_name) + 1
    
    st.markdown("---")

# --- 6. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.title("📊 Sales Monitoring System")
    st.divider()
    
    st.warning("👈 **กรุณามองไปที่แถบสีเทาด้านซ้ายมือ** แล้วเลือกแบรนด์เพื่อเริ่มทำงาน")
    
    # ถ้ามองไม่เห็น Sidebar จริงๆ ให้กดปุ่มนี้เพื่อแก้ขัด
    if st.button("ไม่เห็นเมนูทางซ้าย? กดตรงนี้เพื่อกางออก"):
        st.session_state.sidebar_active = True
        st.rerun()
    st.stop()

# --- 7. DASHBOARD ---
st.header(f"📈 ข้อมูลแบรนด์: {selected_brand}")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 ตั้งค่าการมองเห็นสาขา", expanded=False):
            query = st_keyup("🔍 ค้นหา...", key=f"f_{selected_brand}").strip().lower()
            
            m_key = f"m_{selected_brand}"
            def sync_all():
                for s in unique_shops: st.session_state[f"tg_{selected_brand}_{s}"] = st.session_state[m_key]
            
            is_all_on = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("เปิดทั้งหมด", value=is_all_on, key=m_key, on_change=sync_all)
            
            for shop in unique_shops:
                if query and query not in shop.lower(): continue
                t_key = f"tg_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                st.toggle(shop, key=t_key)
            
            if st.button("Save Settings", use_container_width=True, type="primary"):
                all_configs[selected_brand] = {s: st.session_state.get(f"tg_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("บันทึกแล้ว")
                st.rerun()

    # Heatmap
    mask = (raw_df['sync_date'].dt.month == m) & (raw_df['sync_date'].dt.year == y)
    df_f = raw_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid = pd.DataFrame("N/A", index=unique_shops, columns=range(1, last_day + 1))

    if not df_f.empty:
        df_f['Day'] = df_f['sync_date'].dt.day
        for s in unique_shops:
            if not current_settings.get(s, True): grid.loc[s] = "DISABLED"
        for _, r in df_f.iterrows():
            if r['shop_name'] in grid.index and grid.at[r['shop_name'], r['Day']] != "DISABLED":
                stc = r['status_code']
                grid.at[r['shop_name'], r['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    def style_cells(v):
        if v == "✅": return 'background-color: #d4edda;'
        if v == "⚠️": return 'background-color: #fff3cd;'
        if v == "❌": return 'background-color: #f8d7da;'
        if v == "DISABLED": return 'background-color: #e2e8f0; color: transparent;'
        return 'color: #ccc;'

    st.dataframe(grid.style.map(style_cells), use_container_width=True, height=600)
else:
    st.warning("ไม่พบข้อมูล")
