import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="Sales Monitoring Heatmap", layout="wide")

st.markdown("""
    <style>
    /* 1. Sidebar Top Alignment & Compact Layout */
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* 2. Main Container Padding Control */
    .block-container { 
        padding-top: 2rem !important; 
        padding-left: 1rem !important;   
        padding-right: 1rem !important;  
        padding-bottom: 0rem !important; 
    }

    /* 3. Premium Date Card Style */
    .date-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
        margin-top: 10px; margin-bottom: 20px;
        text-align: center;
    }
    .date-card .day-name { color: #ff4b4b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #1f1f1f; line-height: 1; margin: 5px 0; }
    .date-card .month-year { color: #555; font-size: 1rem; }

    /* 4. Strong Typography for Shop Names & Headers */
    [data-testid="stDataFrame"] td:first-child, 
    [data-testid="stDataFrame"] th [data-testid="stText"] {
        font-weight: 900 !important; color: #000000 !important;
    }
    [data-testid="stDataFrame"] td { text-align: center !important; }
    
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONSTANTS & DATA FETCHING ---
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
    except Exception:
        pass
    return pd.DataFrame()

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    now = datetime.now()
    
    # Date Display (Top Section)
    st.markdown(f"""
        <div class="date-card">
            <div class="day-name">{now.strftime('%A')}</div>
            <div class="date-number">{now.day}</div>
            <div class="month-year">{now.strftime('%B %Y')}</div>
            <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
            <div style="font-size: 0.75rem; color: #28a745; font-weight: bold;">● SYSTEM ONLINE</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Selection Controls
    st.header("ตัวเลือก")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))
    
    st.divider()
    y = st.selectbox("ปี (Year)", [2025, 2026], index=1)
    month_list = list(calendar.month_name)[1:]
    m_name = st.selectbox("เดือน (Month)", month_list, index=now.month-1)
    m = month_list.index(m_name) + 1
    
    st.divider()
    st.subheader("📊 สรุปภาพรวม")
    summary_placeholder = st.empty()

# --- 4. DATA PROCESSING ---
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
API_URL = f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}"
full_df = get_data_from_api(API_URL)

if not full_df.empty:
    # Filter Data
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()

    # Create Grid Structure
    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    shops = sorted(full_df['shop_name'].unique())
    grid_df = pd.DataFrame("N/A", index=shops, columns=days)

    # Populate Data (Fast Mapping)
    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for _, row in df_filtered.iterrows():
            if row['shop_name'] in grid_df.index:
                status = row['status_code']
                emoji = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                grid_df.at[row['shop_name'], row['Day']] = emoji

    # Sidebar Metrics Calculation
    count_normal = (grid_df == "✅").sum().sum()
    count_issue = (grid_df == "⚠️").sum().sum() + (grid_df == "❌").sum().sum()
    
    with summary_placeholder.container():
        st.info(f"เดือนนี้มีทั้งหมด {last_day} วัน")
        c1, c2 = st.columns(2)
        c1.metric("ปกติ (✅)", f"{int(count_normal)}")
        c2.metric("ปัญหา (⚠️/❌)", f"{int(count_issue)}")
        
        # Problematic Shops Analysis
        prob_sum = (grid_df == "❌").sum(axis=1) + (grid_df == "⚠️").sum(axis=1)
        top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
        
        if not top_prob.empty:
            st.write("**⚠️ สาขาที่พบปัญหาบ่อย:**")
            for shop, count in top_prob.items():
                st.write(f"- {shop}: `{int(count)}` ครั้ง")
        else:
            st.success("🎉 ยังไม่พบปัญหาในเดือนนี้")

    # --- 5. HEATMAP RENDERING ---
    def apply_cell_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        return 'color: #ced4da;' # N/A remains subtle

    styled_df = grid_df.style.map(apply_cell_style)
    col_config = {d: st.column_config.Column(width=32) for d in days}

    st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=min(len(shops) * 38 + 100, 850), 
        column_config=col_config
    )
    st.caption("✅ ปกติ | ⚠️ ยอดไม่ตรง | ❌ ไม่เข้า | N/A: ยังไม่มีข้อมูล")

else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์หรือเดือนที่เลือก")
