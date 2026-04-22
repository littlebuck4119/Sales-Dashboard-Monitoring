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
    [data-testid="stDataFrame"] { width: 100% !important; }
    
    /* ปรับแต่งปุ่มใน Sidebar ให้ดูเล็กลงประหยัดพื้นที่ */
    div.stButton > button {
        padding: 2px 10px !important;
        font-size: 14px !important;
    }

    .date-card { background-color: #ffffff; padding: 20px 15px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0px 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; text-align: center; }
    .date-card .day-name { color: #ff4b4b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #1f1f1f; line-height: 1; margin: 8px 0; }
    
    /* แก้ไขสีปุ่มบันทึก (Primary) ให้เป็นสีเขียว */
    button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    
    .problem-item { font-size: 0.85rem; line-height: 1.4; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

def get_config():
    try:
        res = requests.get(CONFIG_API, timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_config(full_config):
    requests.post(CONFIG_API, json=full_config)

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
    except Exception: pass
    return pd.DataFrame()

# --- 3. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="date-card">
            <div class="day-name">{now.strftime('%A')}</div>
            <div class="date-number">{now.day}</div>
            <div style="font-size: 0.75rem; color: #28a745; font-weight: bold;">● SYSTEM ONLINE</div>
        </div>
    """, unsafe_allow_html=True)
    
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1
    
    summary_placeholder = st.empty()

# --- 4. MAIN CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    shops = sorted(full_df['shop_name'].unique())
    grid_df = pd.DataFrame("N/A", index=shops, columns=days)

    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    # --- Setting ใน Sidebar ---
    with st.sidebar:
        st.markdown("---")
        with st.expander(f"🚫 **จัดการสาขา: {selected_brand}**"):
            
            # ดีไซน์ประหยัดพื้นที่: รวมคำอธิบายและปุ่มเลือกทั้งหมดไว้แถวเดียวกัน
            st.write("สถานะ Monitor:")
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.caption("เปิด/ปิด ทั้งหมด:")
            if c2.button("✅", help="เปิดทุกสาขา", use_container_width=True):
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = True
                st.rerun()
            if c3.button("❌", help="ปิดทุกสาขา", use_container_width=True):
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = False
                st.rerun()

            st.markdown("---")
            updated_brand_settings = brand_settings.copy()
            for shop in shops:
                key = f"tog_{selected_brand}_{shop}"
                if key not in st.session_state:
                    st.session_state[key] = brand_settings.get(shop, True)
                
                new_val = st.toggle(f"{shop}", key=key)
                updated_brand_settings[shop] = new_val
            
            # ปุ่มบันทึกเป็นสีเขียว (Primary)
            if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True):
                current_full_config[selected_brand] = updated_brand_settings
                save_config(current_full_config)
                st.success("บันทึกแล้ว!")
                st.rerun()

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            shop_name = row['shop_name']
            if shop_name in grid_df.index:
                if not brand_settings.get(shop_name, True):
                    grid_df.loc[shop_name] = "DISABLED"
                else:
                    status = row['status_code']
                    emoji = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                    grid_df.at[shop_name, row['Day']] = emoji

    # สรุปผล
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    c_prob_shops = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum() if not active_grid.empty else 0
    
    with summary_placeholder.container():
        st.info(f"Monitor: **{len(active_shops)}** / **{len(shops)}** สาขา")
        m1, m2 = st.columns(2)
        m1.metric("ปกติ ✅", len(active_shops) - c_prob_shops)
        m2.metric("ปัญหา ⚠️/❌", c_prob_shops)

    # --- 5. STYLING ---
    def apply_cell_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(
        grid_df.style.map(apply_cell_style), 
        use_container_width=True, 
        height=min(len(shops) * 38 + 100, 850), 
        column_config={d: st.column_config.Column(width=30) for d in days}
    )
else:
    st.warning("⚠️ ไม่พบข้อมูล")
