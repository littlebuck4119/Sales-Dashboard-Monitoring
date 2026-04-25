import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CORE CONFIG ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" # บังคับกางเมนู
)

# --- 2. THEME & CURSOR REMOVER ---
st.markdown("""
    <style>
    /* ฆ่า Cursor กระพริบถาวรทุกจุด */
    * { caret-color: transparent !important; }
    input { caret-color: transparent !important; }
    
    /* ซ่อนส่วนเกิน */
    header, footer { visibility: hidden !important; }

    /* ปรับแต่ง Sidebar ให้ดูหรู (Modern Enterprise) */
    [data-testid="stSidebarContent"] {
        background-color: #f8fafc !important;
        padding-top: 1rem !important;
    }
    
    /* การ์ดวันที่ */
    .sb-date-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA UTILS ---
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

# --- 4. SIDEBAR NAVIGATION (กดได้แน่นอน) ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="sb-date-card">
            <div style="font-size: 0.7rem; color: #94a3b8; font-weight: bold; letter-spacing: 0.1em;">DASHBOARD STATUS</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("📁 Brand Settings")
    brand_list = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("Select Target Brand", brand_list, index=0)
    
    c1, c2 = st.columns(2)
    with c1: target_y = st.selectbox("Year", [2025, 2026], index=1)
    with c2:
        m_names = list(calendar.month_name)[1:]
        m_target_name = st.selectbox("Month", m_names, index=now.month-1)
        target_m = m_names.index(m_target_name) + 1

    summary_st = st.empty()
    st.markdown("---")

# --- 5. MAIN CONTENT (Professional Landing) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    # ใช้ฟีเจอร์มาตรฐานของ Streamlit ทำหน้า Welcome เพื่อไม่ให้ขวางปุ่ม
    st.title("📊 Sales Monitoring System")
    st.write("---")
    
    col_msg, col_img = st.columns([1, 1])
    with col_msg:
        st.markdown("""
        ### Welcome to Enterprise Intelligence
        Please select a brand from the **Sidebar menu on the left** to start monitoring daily sales performance.
        
        **System Capabilities:**
        * Real-time status tracking (Sync Status)
        * Branch-level visibility management
        * Monthly performance heatmap
        """)
        st.info("💡 **Tip:** Use the 'Manage Branches' section in the sidebar to toggle branch visibility.")
    
    with col_img:
        # ใช้พื้นหลังโทนเข้มแบบโปรผ่าน st.container
        st.markdown("""
        <div style="background: #0f172a; padding: 40px; border-radius: 20px; color: white; text-align: center;">
            <h2 style="color: #38bdf8; margin-bottom: 10px;">Ready to Analyze</h2>
            <p style="color: #94a3b8;">Waiting for brand selection...</p>
            <div style="font-size: 60px; margin-top: 20px;">⚡</div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD VIEW ---
st.title(f"📈 {selected_brand} Performance")
raw_df = fetch_api_data(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not raw_df.empty:
    unique_shops = sorted(raw_df['shop_name'].unique())
    all_configs = get_config()
    current_settings = all_configs.get(selected_brand, {})

    with st.sidebar:
        with st.expander("🚫 Visibility Settings", expanded=False):
            query = st_keyup("🔍 Search...", key=f"f_{selected_brand}").strip().lower()
            
            m_key = f"m_tg_{selected_brand}"
            def sync_all():
                for s in unique_shops: st.session_state[f"tg_{selected_brand}_{s}"] = st.session_state[m_key]
            
            is_all_on = all(current_settings.get(s, True) for s in unique_shops)
            st.toggle("Toggle All", value=is_all_on, key=m_key, on_change=sync_all)
            
            new_settings = {}
            for shop in unique_shops:
                if query and query not in shop.lower(): continue
                t_key = f"tg_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = current_settings.get(shop, True)
                new_settings[shop] = st.toggle(shop, key=t_key)
            
            if st.button("Save Configuration", type="primary", use_container_width=True):
                all_configs[selected_brand] = {s: st.session_state.get(f"tg_{selected_brand}_{s}", True) for s in unique_shops}
                save_config(all_configs)
                st.success("Config Saved!")
                st.rerun()

    # Heatmap Processing
    mask = (raw_df['sync_date'].dt.month == target_m) & (raw_df['sync_date'].dt.year == target_y)
    df_filtered = raw_df[mask].copy()
    _, last_day = calendar.monthrange(target_y, target_m)
    heatmap_grid = pd.DataFrame("N/A", index=unique_shops, columns=range(1, last_day + 1))

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in unique_shops:
            if not current_settings.get(shop, True): heatmap_grid.loc[shop] = "DISABLED"
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in heatmap_grid.index and heatmap_grid.at[row['shop_name'], row['Day']] != "DISABLED":
                stc = row['status_code']
                heatmap_grid.at[row['shop_name'], row['Day']] = "✅" if stc == 2 else "⚠️" if stc == 1 else "❌"

    with summary_st.container():
        st.write(f"**Monitoring:** {sum(current_settings.get(s, True) for s in unique_shops)} Branches")

    def cell_style(v):
        if v == "✅": return 'background-color: #dcfce7; color: #166534;'
        if v == "⚠️": return 'background-color: #fef9c3; color: #854d0e;'
        if v == "❌": return 'background-color: #fee2e2; color: #991b1b;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;' 
        return 'color: #cbd5e1;'

    st.dataframe(heatmap_grid.style.map(cell_style), use_container_width=True, height=750)
else:
    st.warning("No data found.")
