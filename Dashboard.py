import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & NEW LIGHT THEME STYLES ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* 폰ต์และพื้นหลังหลัก */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8fbad !important; /* พื้นหลังฟ้าอ่อนจางๆ */
    }

    /* ปรับแต่ง Main Content Area */
    [data-testid="stMain"] {
        background: #fcfdfe !important;
    }

    /* Sidebar - เปลี่ยนเป็นโทนเทา-ฟ้าอ่อน */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* ซ่อน Cursor กระพริบตามสั่ง */
    * { caret-color: transparent !important; }

    /* ปรับแต่งหัวข้อ */
    h1, h2, h3 {
        color: #1e293b !important;
        font-weight: 800 !important;
    }

    /* Metric Cards ใน Sidebar */
    [data-testid="stMetric"] {
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    /* Welcome Hero Section (ปรับเป็นโทนสว่าง) */
    .welcome-hero {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        border-radius: 24px !important;
        padding: 60px !important;
    }

    .welcome-title {
        background: linear-gradient(90deg, #0284c7 0%, #3b82f6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    /* ปุ่มบันทึก */
    button[kind="primary"] {
        background: #0284c7 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* ตกแต่งการ์ดปัญหา */
    .problem-item {
        background-color: #fff1f2 !important;
        border-left: 4px solid #f43f5e !important;
        color: #881337 !important;
        border-radius: 8px !important;
    }

    /* จัดการช่องว่างหน้าจอ */
    .block-container { padding-top: 2rem !important; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING (เหมือนเดิม) ---
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

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div style="background-color: #f0f9ff; padding: 15px; border-radius: 12px; border: 1px solid #bae6fd; margin-bottom: 20px;">
            <div style="font-size: 0.75rem; color: #0369a1; font-weight: 700; text-transform: uppercase;">System Ready</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: #0c4a6e;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()

# --- 4. MAIN CONTENT (Welcome View) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; min-height: 80vh;">
            <div class="welcome-hero" style="text-align: center; max-width: 800px;">
                <div style="font-size: 0.8rem; background: #e0f2fe; color: #0369a1; padding: 5px 15px; border-radius: 50px; display: inline-block; margin-bottom: 20px; font-weight: 700;">SALES MONITORING v2.0</div>
                <h1 class="welcome-title" style="font-size: 3.5rem; margin-bottom: 15px;">Monitoring<br>Intelligence</h1>
                <p style="color: #64748b; font-size: 1.1rem; line-height: 1.6; margin-bottom: 40px;">
                    ยินดีต้อนรับสู่ระบบติดตามข้อมูลยอดขายสาขาแบบเรียลไทม์<br>
                    เลือกแบรนด์จากเมนูด้านซ้ายเพื่อเริ่มต้นวิเคราะห์ข้อมูล
                </p>
                <div style="display: flex; gap: 15px; justify-content: center;">
                    <div style="background: #f1f5f9; padding: 15px 25px; border-radius: 15px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">4</div>
                        <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Brands</div>
                    </div>
                    <div style="background: #f1f5f9; padding: 15px 25px; border-radius: 15px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">Real-time</div>
                        <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Status</div>
                    </div>
                </div>
                <div style="margin-top: 40px; color: #94a3b8; font-style: italic; font-size: 0.9rem;">← กรุณาเลือกแบรนด์ที่เมนู Sidebar</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW ---
st.markdown(f"<h2 style='margin-bottom: 25px;'>📈 {selected_brand} Performance</h2>", unsafe_allow_html=True)
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("⚙️ ตั้งค่าการมองเห็นสาขา", expanded=False):
            search_query = st_keyup("ค้นหาสาขา...", key=f"k_{selected_brand}").strip().lower()
            
            master_key = f"m_{selected_brand}"
            def on_master():
                for s in shops: st.session_state[f"t_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("เลือกทั้งหมด", value=all_on, key=master_key, on_change=on_master)
            
            updated = {s: st.session_state.get(f"t_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}
            filtered = [s for s in shops if search_query in s.lower()] if search_query else shops

            for shop in filtered:
                t_key = f"t_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated[shop] = st.toggle(shop, key=t_key)

            if st.button("💾 บันทึกการตั้งค่า", use_container_width=True, type="primary"):
                current_full_config[selected_brand] = updated
                save_config(current_full_config)
                st.success("บันทึกแล้ว!")
                st.rerun()

    # Data Processing
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid_df = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in shops:
            if not brand_settings.get(shop, True): grid_df.loc[shop] = "DISABLED"
        for _, row in df_filtered.iterrows():
            s_name, d, status = row['shop_name'], row['Day'], row['status_code']
            if s_name in grid_df.index and grid_df.at[s_name, d] != "DISABLED":
                grid_df.at[s_name, d] = "✅" if status == 2 else "⚠️" if status == 1 else "❌"

    # Sidebar Summary
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    with summary_placeholder.container():
        st.markdown(f"**กำลังตรวจสอบ: {len(active_shops)} สาขา**")
        m1, m2 = st.columns(2)
        if not active_grid.empty:
            prob_rows = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("เสถียร ✅", len(active_shops) - prob_rows)
            m2.metric("มีปัญหา ⚠️", prob_rows, delta_color="inverse")
            
            probs = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top = probs[probs > 0].sort_values(ascending=False).head(3)
            if not top.empty:
                st.markdown("---")
                for shop, count in top.items():
                    st.markdown(f'<div class="problem-item"><b>{shop}</b><br>พบจุดบกพร่อง {int(count)} ครั้ง</div>', unsafe_allow_html=True)

    # Apply Heatmap Styles
    def style_ui(v):
        if v == "✅": return 'background-color: #f0fdf4; color: #166534; font-weight: bold; border: 1px solid #dcfce7;'
        if v == "⚠️": return 'background-color: #fffbeb; color: #92400e; font-weight: bold; border: 1px solid #fef3c7;'
        if v == "❌": return 'background-color: #fef2f2; color: #991b1b; font-weight: bold; border: 1px solid #fee2e2;'
        if v == "DISABLED": return 'background-color: #f8fafc; color: transparent; border: none;'
        return 'color: #e2e8f0; font-size: 10px;'

    st.dataframe(grid_df.style.map(style_ui), use_container_width=True, height=750,
                 column_config={d: st.column_config.Column(width=35) for d in range(1, last_day + 1)})
else:
    st.warning("ไม่มีข้อมูลสำหรับแบรนด์ที่เลือก")
