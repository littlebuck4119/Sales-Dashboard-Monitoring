import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- 1. CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# CSS: ล็อคทุกอย่างตามสั่ง (Sidebar ชิดบน / ตัวหนังสือเข้ม / สีตารางชัด)
st.markdown("""
    <style>
    /* Sidebar ชิดขอบบน */
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* หน้าหลัก Padding 1rem ตามเดิม */
    .block-container { 
        padding-top: 2rem !important; 
        padding-left: 1rem !important;   
        padding-right: 1rem !important;  
        padding-bottom: 0rem !important; 
    }

    /* Date Card */
    .date-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
        margin-top: 10px; 
        margin-bottom: 20px;
        text-align: center;
    }

    /* บังคับตัวหนังสือสาขา (คอลัมน์แรก) และวันที่ (หัวตาราง) ให้ดำเข้ม */
    [data-testid="stDataFrame"] td:first-child, 
    [data-testid="stDataFrame"] th [data-testid="stText"] {
        font-weight: 900 !important; 
        color: #000000 !important;
        font-size: 14px !important;
    }
    
    /* จัดตัวเลขวันที่ให้เด่น */
    [data-testid="stDataFrame"] th { background-color: #f0f2f6 !important; }

    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
}

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

# --- 2. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div class="date-card">
            <div class="day-name">{now.strftime('%A')}</div>
            <div class="date-number">{now.day}</div>
            <div class="month-year">{now.strftime('%B %Y')}</div>
            <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
            <div style="font-size: 0.75rem; color: #28a745; font-weight: bold;">● SYSTEM ONLINE</div>
        </div>
    """, unsafe_allow_html=True)
    
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=now.month-1)
    m = month_names.index(m_name) + 1
    
    summary_placeholder = st.empty()

# --- 3. MAIN CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    _, last_day = calendar.monthrange(y, m)
    days_in_month = list(range(1, last_day + 1))
    shop_list = sorted(full_df['shop_name'].unique())
    grid_df = pd.DataFrame(None, index=shop_list, columns=days_in_month)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index:
                grid_df.at[row['shop_name'], row['Day']] = row['status_code']

    # สรุปใน Sidebar
    c_ok = (grid_df == 2).sum().sum()
    c_err = (grid_df == 0).sum().sum() + (grid_df == 1).sum().sum()
    with summary_placeholder.container():
        st.metric("ปกติ (✅)", f"{int(c_ok)}")
        st.metric("ปัญหา (⚠️/❌)", f"{int(c_err)}")

    # --- 4. STYLE THE TABLE (กลับมาใช้สีเข้มๆ) ---
    def style_heatmap(val):
        if val == 2: return 'background-color: #d4edda; color: #155724; text-align: center;' # เขียวเข้ม
        if val == 1: return 'background-color: #fff3cd; color: #856404; text-align: center;' # เหลือง
        if val == 0: return 'background-color: #f8d7da; color: #721c24; text-align: center;' # แดง
        return 'background-color: #ffffff; color: #dee2e6; text-align: center;' # N/A จางๆ

    def format_emoji(val):
        if val == 2: return "✅"
        if val == 1: return "⚠️"
        if val == 0: return "❌"
        return "N/A"

    # จัดการการแสดงผล
    styled_df = grid_df.style.map(style_heatmap).format(format_emoji)

    st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=min(len(shop_list) * 38 + 100, 800), 
        column_config={day: st.column_config.Column(width=35) for day in days_in_month}
    )
else:
    st.warning("⚠️ ไม่พบข้อมูล")
