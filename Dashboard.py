import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG: บังคับกาง Sidebar ตลอดเวลา ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # กางรอไว้เลยครับพี่ ไม่ต้องหาทางกดเปิดเอง
)

# --- 2. CSS: ปรับให้ Sidebar และหน้า Welcome อยู่ด้วยกันได้ ---
st.markdown("""
    <style>
    /* ซ่อน Header/Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* สไตล์ Sidebar ให้ดูดี */
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .date-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
    
    /* สไตล์สำหรับรายการปัญหา */
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
        <div class="date-card">
            <div style="color: #666; font-size: 0.8rem;">📅 TODAY</div>
            <div style="font-weight: bold; font-size: 1.1rem;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์ที่ต้องการ", brand_options, index=0)
    
    st.markdown("---")
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()

# --- 5. MAIN CONTENT ---

if selected_brand == "🛑 SELECT BRAND 🛑":
    # หน้า Welcome แบบระเบิดขอบ แต่ไม่ทับ Sidebar
    st.markdown("""
        <style>
        [data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
        .welcome-bg {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
        }
        </style>
        <div class="welcome-bg">
            <h1 style="font-size: 4rem; font-weight: 800; margin-bottom: 0;">Sales Monitoring System</h1>
            <p style="font-size: 1.5rem; opacity: 0.8; margin-top: 10px;">👈 กดทางซ้ายเพื่อเลือก Brand</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD MODE ---
# คืนค่า Padding ให้หน้าตาราง
st.markdown("<style>[data-testid='stAppViewBlockContainer'] { padding: 2rem !important; background: white; color: black; }</style>", unsafe_allow_html=True)

st.header(f"📈 {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})
    shops = sorted(full_df['shop_name'].unique())

    # --- Sidebar Management (Toggle) ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา"):
            search = st_keyup("🔍 ค้นหา...", key=f"s_{selected_brand}").strip().lower()
            
            master_key = f"m_{selected_brand}"
            def toggle_all():
                for s in shops: st.session_state[f"t_{selected_brand}_{s}"] = st.session_state[master_key]
            
            st.toggle("🔔 เปิด/ปิด ทั้งหมด", key=master_key, on_change=toggle_all)
            st.markdown("---")
            
            updated = {}
            for s in shops:
                if search and search not in s.lower(): continue
                t_key = f"t_{selected_brand}_{s}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(s, True)
                updated[s] = st.toggle(s, key=t_key)
            
            if st.button("💾 บันทึก", use_container_width=True, type="primary"):
                current_full_config[selected_brand] = updated
                save_config(current_full_config)
                st.success("บันทึกแล้ว!")
                st.rerun()

    # --- Data Grid ---
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_f = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    grid = pd.DataFrame("N/A", index=shops, columns=range(1, last_day + 1))

    if not df_f.empty:
        df_f['Day'] = df_f['sync_date'].dt.day
        for s in shops:
            if not brand_settings.get(s, True): grid.loc[s] = "DISABLED"
        for _, r in df_f.iterrows():
            sn, d, sc = r['shop_name'], r['Day'], r['status_code']
            if sn in grid.index and grid.at[sn, d] != "DISABLED":
                grid.at[sn, d] = "✅" if sc == 2 else "⚠️" if sc == 1 else "❌"

    # --- Summary ---
    with summary_placeholder.container():
        actives = [s for s in shops if brand_settings.get(s, True)]
        st.info(f"Active: {len(actives)} / {len(shops)}")

    def style_grid(v):
        if v == "✅": return 'background-color: #d4edda;'
        if v == "⚠️": return 'background-color: #fff3cd;'
        if v == "❌": return 'background-color: #f8d7da;'
        if v == "DISABLED": return 'background-color: #6c757d; color: transparent;'
        return 'color: #eeeeee;'

    st.dataframe(grid.style.map(style_grid), use_container_width=True, height=750)
