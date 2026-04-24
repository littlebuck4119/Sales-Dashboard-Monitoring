import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & STYLES ---
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# CSS หลัก (รวมทั้งหน้า Welcome และ Dashboard)
st.markdown("""
    <style>
    /* ซ่อน Header และ Footer มาตรฐาน */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* สไตล์สำหรับรายการปัญหาใน Sidebar */
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    
    /* สไตล์สำหรับ Card วันที่ใน Sidebar */
    .date-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
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
    st.markdown(f"""
        <div class="date-card">
            <div style="color: #666; font-size: 0.8rem;">📅 TODAY</div>
            <div style="font-weight: bold; font-size: 1.1rem;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()

# --- 4. MAIN CONTENT ---

if selected_brand == "🛑 SELECT BRAND 🛑":
    # ไม้ตายระเบิดขอบ + 2 บรรทัดกลางหน้าจอ
    st.markdown("""
        <style>
        [data-testid="stAppViewBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
        .welcome-bg {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            height: 100vh;
            width: 100vw;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
        }
        </style>
        <div class="welcome-bg">
            <h1 style="font-size: 4.5rem; font-weight: 800; margin-bottom: 0px; letter-spacing: -1px;">
                Sales Monitoring System
            </h1>
            <p style="font-size: 1.5rem; opacity: 0.8; margin-top: 10px;">
                👈 กดทางซ้ายเพื่อเลือก Brand
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD MODE (เมื่อเลือกแบรนด์แล้ว) ---
# คืนค่า Padding ให้หน้า Dashboard เพื่อความสวยงาม
st.markdown("<style>[data-testid='stAppViewBlockContainer'] { padding: 2rem !important; }</style>", unsafe_allow_html=True)

st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})
    shops = sorted(full_df['shop_name'].unique())

    # --- ส่วนจัดการสาขาใน Sidebar ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"src_{selected_brand}").strip().lower()
            
            master_key = f"ms_{selected_brand}"
            def on_ms_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 เปิด/ปิด ทั้งหมด", value=all_on, key=master_key, on_change=on_ms_change)
            
            st.markdown("---")
            updated_settings = {}
            for shop in shops:
                if search_query and search_query not in shop.lower(): continue
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    # --- ตาราง Heatmap ---
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid_df = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for s in shops:
            if not brand_settings.get(s, True): grid_df.loc[s] = "DISABLED"
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index and grid_df.at[row['shop_name'], row['Day']] != "DISABLED":
                stc = row['status_code']
                grid_df.at[row['shop_name'], row['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌" if stc == 0 else "N/A"

    # --- สรุปภาพรวม (Sidebar) ---
    with summary_placeholder.container():
        active_list = [s for s in shops if brand_settings.get(s, True)]
        st.info(f"Monitor: **{len(active_list)}** / **{len(shops)}** สาขา")
        if active_list:
            active_grid = grid_df.loc[active_list]
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1, m2 = st.columns(2)
            m1.metric("ปกติ ✅", len(active_list) - prob_count)
            m2.metric("ปัญหา ⚠️/❌", prob_count)

    # --- Styling ตาราง ---
    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ ไม่พบข้อมูล")
