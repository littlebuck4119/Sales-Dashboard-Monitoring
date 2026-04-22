import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 1.2rem !important; }
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-bottom: 0rem !important; }
    .date-card { background-color: #ffffff; padding: 20px 15px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0px 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; text-align: center; }
    .date-card .day-name { color: #ff4b4b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #1f1f1f; line-height: 1; margin: 8px 0; }
    [data-testid="stDataFrame"] td:first-child { font-weight: 900 !important; color: #000000 !important; }
    [data-testid="stDataFrame"] td { text-align: center !important; }
    .problem-item { font-size: 0.85rem; line-height: 1.4; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการ API ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
}

CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

@st.cache_data(ttl=60)
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

def get_config():
    try:
        res = requests.get(CONFIG_API, timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_config(full_config):
    requests.post(CONFIG_API, json=full_config)

# --- 3. SIDEBAR (ส่วนเลือกแบรนด์ก่อน) ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="date-card">
            <div class="day-name">{now.strftime('%A')}</div>
            <div class="date-number">{now.day}</div>
            <div style="font-size: 0.75rem; color: #28a745; font-weight: bold;">● SYSTEM ONLINE</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### **ตัวเลือก**")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    st.markdown("### **📊 สรุปภาพรวม**")
    summary_placeholder = st.empty()

# --- 4. MAIN CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
# ดึงข้อมูลยอดขาย
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    shops = sorted(full_df['shop_name'].unique())
    grid_df = pd.DataFrame("N/A", index=shops, columns=days)

    # ดึง Config เปิด/ปิด
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    # สร้าง Toggle ใน Sidebar (ย้ายมาไว้ตรงนี้เพราะต้องใช้ตัวแปร shops)
    with st.sidebar:
        st.markdown("---")
        with st.expander(f"⚙️ **ตั้งค่าปิดสาขา: {selected_brand}**"):
            updated_brand_settings = brand_settings.copy()
            for shop in shops:
                is_active = brand_settings.get(shop, True)
                new_val = st.toggle(f"{shop}", value=is_active, key=f"tog_{selected_brand}_{shop}")
                updated_brand_settings[shop] = new_val
            
            if st.button("💾 บันทึกการตั้งค่า"):
                current_full_config[selected_brand] = updated_brand_settings
                save_config(current_full_config)
                st.success("บันทึกแล้ว!")
                st.rerun()

    # วาดข้อมูลลงตาราง
    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            shop = row['shop_name']
            if shop in grid_df.index:
                # ถ้าปิดสาขานี้ไว้ ให้โชว์ OFF
                if not brand_settings.get(shop, True):
                    grid_df.loc[shop] = "OFF"
                else:
                    status = row['status_code']
                    emoji = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                    grid_df.at[shop, row['Day']] = emoji

    # สรุปผล (เฉพาะสาขาที่เปิด)
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    
    with summary_placeholder.container():
        st.info(f"Monitor: **{len(active_shops)}** / ทั้งหมด: **{len(shops)}** สาขา")
        m1, m2 = st.columns(2)
        if not active_grid.empty:
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("ปกติ ✅", len(active_shops) - prob_count)
            m2.metric("ปัญหา ⚠️/❌", prob_count)
        else:
            m1.metric("ปกติ ✅", 0)
            m2.metric("ปัญหา ⚠️/❌", 0)

    # แสดงผลตาราง
    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "OFF": return 'background-color: #f1f3f5; color: #adb5bd; font-style: italic;'
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800)
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์หรือเดือนที่เลือก")
