import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- 1. CONFIG ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

# CSS: Sidebar ชิดบน / หน้าหลัก Padding เท่าเดิมตามสั่ง
st.markdown("""
    <style>
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    .block-container { 
        padding-top: 2rem !important; 
        padding-left: 1rem !important;   
        padding-right: 1rem !important;  
        padding-bottom: 0rem !important; 
    }
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
    .date-card .day-name { color: #ff4b4b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #1f1f1f; line-height: 1; margin: 5px 0; }
    .date-card .month-year { color: #555; font-size: 1rem; }
    [data-testid="stDataFrame"] td:first-child, [data-testid="stDataFrame"] th {
        font-weight: 900 !important; color: #000000 !important;
    }
    [data-testid="stDataFrame"] td { text-align: center !important; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee", 
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
}

# --- 2. FAST DATA FETCHING ---
@st.cache_data(ttl=300)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df['sync_date'] = pd.to_datetime(df['sync_date'])
                return df
    except: pass
    return pd.DataFrame()

# --- 3. SIDEBAR ---
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
    
    st.header("ตัวเลือก")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    API_URL = f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}"
    
    st.divider()
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_names = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_names, index=now.month-1)
    m = month_names.index(m_name) + 1
    
    st.divider()
    st.subheader("📊 สรุปภาพรวม")
    summary_placeholder = st.empty()

# --- 4. MAIN CONTENT ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")

full_df = get_data_from_api(API_URL)

if full_df is not None and not full_df.empty:
    # 1. กรองข้อมูลตามเดือนและปี
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    # 2. เตรียมโครงสร้างตาราง (บังคับชนิดข้อมูลเป็น Object เพื่อรองรับทั้งเลขและ N/A)
    _, last_day = calendar.monthrange(y, m)
    days_in_month = list(range(1, last_day + 1))
    shop_list = sorted(full_df['shop_name'].unique())
    grid_df = pd.DataFrame("N/A", index=shop_list, columns=days_in_month, dtype=object)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        # 3. ใช้การ Loop แบบลดรูป (รักษาสมดุลความเร็วและความปลอดภัย)
        # วิธีนี้จะไม่เกิด TypeError แบบ .update() เพราะจัดการ Data Type ให้เอง
        pivot_data = df_filtered.groupby(['shop_name', 'Day'])['status_code'].first().unstack()
        for col in pivot_data.columns:
            if col in grid_df.columns:
                grid_df[col].update(pivot_data[col])

    # 4. สรุปใน Sidebar
    count_normal = (grid_df == 2).sum().sum()
    count_warning = (grid_df == 1).sum().sum()
    count_error = (grid_df == 0).sum().sum()
    
    with summary_placeholder.container():
        st.info(f"เดือนนี้มีทั้งหมด {last_day} วัน")
        c1, c2 = st.columns(2)
        c1.metric("ปกติ (✅)", f"{int(count_normal)}")
        c2.metric("ปัญหา (⚠️/❌)", f"{int(count_warning + count_error)}")
        
        # สาขาที่มีปัญหาบ่อย
        problem_counts = (grid_df == 0).sum(axis=1) + (grid_df == 1).sum(axis=1)
        top_problem_shops = problem_counts[problem_counts > 0].sort_values(ascending=False).head(3)
        
        if not top_problem_shops.empty:
            st.write("**⚠️ สาขาที่พบปัญหาบ่อย:**")
            for shop, count in top_problem_shops.items():
                st.write(f"- {shop}: `{int(count)}` ครั้ง")
        else:
            st.success("🎉 ยังไม่พบปัญหาในเดือนนี้")

    # 5. แปลงเป็น Emoji เพื่อความเร็วในการโหลดหน้าเว็บ
    status_map = {2: "✅", 2.0: "✅", 1: "⚠️", 1.0: "⚠️", 0: "❌", 0.0: "❌", "N/A": "N/A"}
    display_df = grid_df.applymap(lambda x: status_map.get(x, x))

    # 6. แสดงผลตาราง
    st.dataframe(
        display_df, 
        use_container_width=True, 
        height=min(len(shop_list) * 38 + 100, 800), 
        column_config={day: st.column_config.Column(width=32) for day in days_in_month}
    )
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์หรือเดือนที่เลือก")
