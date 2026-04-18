import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# 1. Inject CSS: บังคับให้ทุกช่องในตารางจัดวางกึ่งกลางและเอา Padding ส่วนเกินออก
st.markdown("""
    <style>
    /* จัดกึ่งกลางทั้งแนวตั้งและแนวนอน */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    /* บังคับความสูงแถวให้กระชับ */
    [data-testid="stDataFrame"] div[role="gridcell"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
}

with st.sidebar:
    st.header("ตัวเลือก")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    API_URL = f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}"
    st.divider()
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=datetime.now().month-1)
    m = month_names.index(m_name) + 1

st.title(f"📊 {selected_brand} - Sales Monitoring Heatmap")

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
    except:
        return pd.DataFrame()

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

    def format_status(val):
        if val == 2 or val == 2.0: return "✅"
        if val == 1 or val == 1.0: return "⚠️"
        if val == 0 or val == 0.0: return "❌"
        return "N/A"

    def style_grid(val):
        base = 'background-color: #f8f9fa; border: 1px solid #ffffff;'
        if val == "N/A": 
            return base + ' color: #adb5bd; font-size: 8px;'
        return base

    st.subheader(f"🗓️ ประจำเดือน {m_name} {y}")
    styled_grid = grid_df.style.map(style_grid).format(format_status)

    # 2. ตั้งค่าความกว้างคอลัมน์วันที่ (1-31) ให้เล็กจิ๋วที่ 35 พิกเซล
    # วิธีนี้จะบีบช่องให้แคบลงจน Emoji ไม่มีที่ให้เยื้องเลยครับ
    col_config = {day: st.column_config.Column(width=35) for day in days_in_month}
    # สำหรับคอลัมน์ชื่อสาขา ให้กว้างตามปกติ
    col_config[None] = st.column_config.Column(width="medium")

    st.dataframe(
        styled_grid, 
        use_container_width=True, 
        height=800,
        column_config=col_config
    )
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
else:
    st.warning(f"⚠️ ไม่พบข้อมูลของ {selected_brand}")
