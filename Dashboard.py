import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# CSS: บังคับทุกอย่างให้ชิดขอบบนและจัดการ Sidebar
st.markdown("""
    <style>
    /* 1. ดันเนื้อหา Sidebar ขึ้นไปชิดขอบบนสุด */
    [data-testid="stSidebarContent"] {
        padding-top: 0.5rem !important;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* 2. จัดการระยะห่างใน Sidebar ให้กระชับ */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }

    /* 3. ดันเนื้อหาฝั่งขวา (ตาราง) ขึ้นชิดบน */
    .block-container { 
        padding-top: 1.5rem !important;
        padding-left: 1rem !important; 
        padding-right: 1rem !important; 
        padding-bottom: 0rem !important; 
    }

    /* 4. สไตล์ตาราง: ตัวหนาและจัดกลาง */
    [data-testid="stDataFrame"] td:first-child, [data-testid="stDataFrame"] th {
        font-weight: 900 !important; color: #000000 !important;
    }
    [data-testid="stDataFrame"] td { text-align: center !important; }

    /* ซ่อน Header/Footer ของ Streamlit */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
}

# --- ดึงข้อมูล ---
@st.cache_data(ttl=10)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df['sync_date'] = pd.to_datetime(df['sync_date'])
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    # แสดง Logo (ปรับเป็น .png เพื่อรองรับพื้นหลังโปร่งใส)
    # ถ้าพี่ยังไม่ได้เปลี่ยนไฟล์ใน GitHub ให้แก้กลับเป็น .JPG นะครับ
    logo_file = "synaturelogo.png" 
    try:
        st.image(logo_file, width=120)
    except:
        st.markdown("### Synature Technology")
    
    # ใช้ markdown แทน header เพื่อให้ระยะห่างข้างบนน้อยลง
    st.markdown("#### **ตัวเลือก**")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    API_URL = f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}"
    
    st.divider()
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1
    
    st.divider()
    st.subheader("📊 สรุปภาพรวม")
    summary_placeholder = st.empty()

# --- MAIN CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")

full_df = get_data_from_api(API_URL)

if full_df is not None and not full_df.empty:
    shop_list = sorted(full_df['shop_name'].unique())
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    _, last_day = calendar.monthrange(y, m)
    days_in_month = [i for i in range(1, last_day + 1)]
    grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month, dtype=object)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index and row['Day'] in grid_df.columns:
                grid_df.at[row['shop_name'], row['Day']] = row['status_code']

    # --- สรุปใน Sidebar ---
    count_normal = (grid_df == 2).sum().sum()
    count_warning = (grid_df == 1).sum().sum()
    count_error = (grid_df == 0).sum().sum()
    
    problem_counts = (grid_df == 0).sum(axis=1) + (grid_df == 1).sum(axis=1)
    top_problem_shops = problem_counts.sort_values(ascending=False).head(3)
    
    with summary_placeholder.container():
        st.info(f"เดือนนี้มีทั้งหมด {last_day} วัน")
        c1, c2 = st.columns(2)
        c1.metric("ปกติ (✅)", f"{count_normal}")
        c2.metric("ปัญหา (⚠️/❌)", f"{count_warning + count_error}")
        
        st.write("**⚠️ สาขาที่มีปัญหามากที่สุด:**")
        problematic_shops = top_problem_shops[top_problem_shops > 0]
        
        if not problematic_shops.empty:
            for shop, count in problematic_shops.items():
                st.write(f"- {shop}: `{count}` ครั้ง")
        else:
            st.success("🎉 ยังไม่พบปัญหาในเดือนนี้")

    # ตาราง Heatmap
    def format_status(val):
        if val == 2 or val == 2.0: return "✅"
        if val == 1 or val == 1.0: return "⚠️"
        if val == 0 or val == 0.0: return "❌"
        return "N/A"

    def style_grid(val):
        base = 'background-color: #f8f9fa; border: 1px solid #ffffff;'
        if val == "N/A": return base + ' color: #adb5bd; font-size: 8px;'
        return base

    styled_grid = grid_df.style.map(style_grid).format(format_status)
    config = {day: st.column_config.Column(width=32) for day in days_in_month}
    config[None] = st.column_config.Column(width="medium")

    st.dataframe(styled_grid, use_container_width=True, height=1000, column_config=config)
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
else:
    st.warning("⚠️ ไม่พบข้อมูล")
