import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & SYSTEM STYLES ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# บังคับ CSS ให้กลืนเป็นชิ้นเดียวกันทั้งแอป (ธีมเขียว Soft)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* 1. พื้นหลังรวม - ไล่เฉดจากเขียว Soft ไปขาวเพื่อให้กลืนกับ Sidebar */
    .stApp {
        background: linear-gradient(90deg, rgb(240, 244, 241) 0%, rgb(248, 250, 252) 100%) !important;
        font-family: 'Inter', sans-serif;
    }

    /* 2. Sidebar - สีเขียว Soft (Sage Green) */
    [data-testid="stSidebar"] {
        background-color: rgb(240, 244, 241) !important;
        border-right: 1px solid rgba(0,0,0,0.05) !important;
    }
    
    /* 3. Main Content Area */
    [data-testid="stMain"], [data-testid="stAppViewContainer"] {
        background-color: transparent !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 5rem !important;
    }

    /* 4. Welcome Card - Format ตามรูปที่ต้องการ (ไม่มีปุ่ม) */
    .welcome-card {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 30px;
        padding: 60px 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.03);
        text-align: center;
        max-width: 800px;
        margin: auto;
    }

    .main-title {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        color: rgb(74, 93, 80) !important; /* เขียว Sage เข้ม */
        margin-top: 15px !important;
        margin-bottom: 5px !important;
        letter-spacing: -1px;
    }

    .sub-title {
        font-size: 1.1rem;
        color: rgb(100, 120, 105);
        line-height: 1.6;
        margin-bottom: 20px;
    }

    /* 5. ตาราง Dashboard & รายการปัญหา */
    .stDataFrame {
        background: white !important;
        border-radius: 15px !important;
        padding: 10px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
    }
    .problem-item { 
        font-size: 0.85rem; 
        padding: 8px 10px; 
        background-color: rgba(255, 255, 255, 0.5); 
        border-left: 4px solid rgb(74, 93, 80); 
        border-radius: 4px; 
        margin-bottom: 6px; 
    }

    /* 6. ส่วนเสริมอื่นๆ */
    * { caret-color: transparent !important; }
    header, footer { visibility: hidden; }
    
    button[kind="primary"] {
        background-color: rgb(74, 93, 80) !important;
        border: none !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA UTILS ---
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
    # การ์ดวันที่ใน Sidebar (ปรับเป็นโทนเขียวขาว)
    st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); margin-bottom: 20px;">
            <div style="font-size: 0.75rem; color: rgb(74, 93, 80); font-weight: 700; text-transform: uppercase;">System Ready</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: rgb(40, 50, 45);">{now.strftime("%A, %d %b %Y")}</div>
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

# --- 4. MAIN CONTENT (หน้า Welcome - ตัดปุ่มออกตามคำขอ) ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; min-height: 70vh;">
            <div class="welcome-card">
                <div style="font-size: 4.5rem; margin-bottom: 0;">📊</div>
                <h1 class="main-title">Sales Monitoring</h1>
                <div style="height: 3px; width: 45px; background: rgb(74, 93, 80); margin: 15px auto 25px; border-radius: 2px;"></div>
                <p class="sub-title">
                    Enterprise Performance Intelligence System<br>
                    <span style="font-size: 0.95rem; opacity: 0.8; color: rgb(74, 93, 80);">
                        กรุณาเลือกแบรนด์ที่เมนูด้านซ้ายเพื่อเริ่มต้นวิเคราะห์ข้อมูล
                    </span>
                </p>
                <div style="margin-top: 30px; padding: 15px; border-top: 1px solid rgba(0,0,0,0.03);">
                    <span style="font-size: 0.85rem; color: rgb(120, 140, 125); font-style: italic;">
                        👈 Control panel is ready on your sidebar
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW (เมื่อเลือกแบรนด์แล้ว) ---
st.markdown(f"<h3 style='color: rgb(74, 93, 80); margin-bottom:1rem;'>📈 {selected_brand} Dashboard</h3>", unsafe_allow_html=True)
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("⚙️ จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"k_{selected_brand}").strip().lower()
            
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
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    # เตรียมตาราง Heatmap
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

    # สรุปภาพรวมใน Sidebar
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    with summary_placeholder.container():
        st.markdown(f"**สถานะ: {len(active_shops)} สาขา**")
        m1, m2 = st.columns(2)
        if not active_grid.empty:
            prob_rows = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("ปกติ ✅", len(active_shops) - prob_rows)
            m2.metric("ปัญหา ⚠️", prob_rows)
            
            # สาขาที่มีปัญหาบ่อย
            prob_sum = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
            if not top_prob.empty:
                st.markdown("---")
                st.write("**⚠️ ปัญหาบ่อยเดือนนี้:**")
                for shop, count in top_prob.items():
                    st.markdown(f'<div class="problem-item"><b>{shop}</b><br>พบปัญหา {int(count)} ครั้ง</div>', unsafe_allow_html=True)

    # ฟังก์ชันระบายสี Heatmap
    def style_heatmap(v):
        if v == "✅": return 'background-color: #f0fdf4; color: #166534; font-weight: bold;'
        if v == "⚠️": return 'background-color: #fffbeb; color: #92400e; font-weight: bold;'
        if v == "❌": return 'background-color: #fef2f2; color: #991b1b; font-weight: bold;'
        if v == "DISABLED": return 'background-color: #f1f5f9; color: transparent;'
        return 'color: #e2e8f0; font-size: 10px;'

    st.dataframe(grid_df.style.map(style_heatmap), use_container_width=True, height=750,
                 column_config={d: st.column_config.Column(width=35) for d in range(1, last_day + 1)})
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์ที่เลือก")
