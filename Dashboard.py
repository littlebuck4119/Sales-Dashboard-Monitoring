import streamlit as st
import pandas as pd
import requests
import calendar
import pymysql
from datetime import datetime

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="Sales Monitoring System", layout="wide")

# เพิ่ม DB CONFIG (สำหรับหน้า Setting)
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "POSAdmin",
    "password": "pospwnet",
    "database": "jonessalad", # จะเปลี่ยนตามแบรนด์ที่เลือกในภายหลัง
    "port": 3307,
    "charset": "utf8"
}

st.markdown("""
    <style>
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    .block-container { padding-top: 2rem !important; }
    .date-card {
        background-color: #ffffff; padding: 20px 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
        text-align: center; margin-bottom: 10px;
    }
    .problem-item {
        font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5;
        border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING (API) ---
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
    except Exception: pass
    return pd.DataFrame()

# --- 3. DATABASE FUNCTIONS (SQL) ---
def get_shop_settings(brand_name):
    # ปรับชื่อ Database ตามแบรนด์ (สมมติว่าชื่อ db ตรงกับแบรนด์ตัวเล็ก)
    db_name = brand_name.lower().replace(" ", "")
    config = DB_CONFIG.copy()
    config['database'] = db_name
    
    try:
        conn = pymysql.connect(**config)
        query = """SELECT ProductLevelID, ProductLevelName, ismonitorsales 
                   FROM productlevel 
                   WHERE deleted = 0 AND isshop = 1 AND showinreport = 1"""
        df = pd.read_sql(query, conn)
        df['ismonitorsales'] = df['ismonitorsales'].astype(bool)
        conn.close()
        return df
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อฐานข้อมูลของ {brand_name} ได้: {e}")
        return pd.DataFrame()

def save_shop_settings(brand_name, df_edited):
    db_name = brand_name.lower().replace(" ", "")
    config = DB_CONFIG.copy()
    config['database'] = db_name
    
    try:
        conn = pymysql.connect(**config)
        cur = conn.cursor()
        for _, row in df_edited.iterrows():
            new_val = 1 if row['ismonitorsales'] else 0
            sql = "UPDATE productlevel SET ismonitorsales = %s WHERE ProductLevelID = %s"
            cur.execute(sql, (new_val, row['ProductLevelID']))
        conn.commit()
        conn.close()
        st.success(f"บันทึกการตั้งค่าของ {brand_name} เรียบร้อยแล้ว!")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึก: {e}")

# --- 4. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""<div class="date-card">
        <div style="color: #ff4b4b; font-weight: bold;">{now.strftime('%A')}</div>
        <div style="font-size: 2.2rem; font-weight: 800;">{now.day}</div>
        <div>{now.strftime('%B %Y')}</div>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("### **เมนูหลัก**")
    menu = st.radio("เลือกหน้าจอ", ["📊 Dashboard", "⚙️ Setting (ปิด-เปิดสาขา)"])
    
    st.markdown("---")
    selected_brand = st.selectbox("เลือกแบรนด์", list(BRAND_CONFIG.keys()))

# --- 5. MAIN CONTENT ---

if menu == "📊 Dashboard":
    st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
    
    # ดึงข้อมูลปี/เดือน (เฉพาะหน้า Dashboard)
    with st.sidebar:
        col_y, col_m = st.columns(2)
        y = col_y.selectbox("ปี", [2025, 2026], index=1)
        month_list = list(calendar.month_name)[1:]
        m_name = col_m.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

    if not full_df.empty:
        mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
        df_filtered = full_df[mask].copy()

        _, last_day = calendar.monthrange(y, m)
        days = list(range(1, last_day + 1))
        shops = sorted(full_df['shop_name'].unique())
        grid_df = pd.DataFrame("N/A", index=shops, columns=days)

        if not df_filtered.empty:
            df_filtered['Day'] = df_filtered['sync_date'].dt.day
            for _, row in df_filtered.iterrows():
                if row['shop_name'] in grid_df.index:
                    status = row['status_code']
                    emoji = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                    grid_df.at[row['shop_name'], row['Day']] = emoji

        # ส่วนสรุปภาพรวมใน Sidebar
        total_unique_shops = len(grid_df)
        has_issue = grid_df.isin(["⚠️", "❌"]).any(axis=1)
        c_prob_shops = has_issue.sum()
        
        with st.sidebar:
            st.markdown("---")
            st.write(f"Monitor ทั้งหมด: **{total_unique_shops}** สาขา")
            st.metric("ปกติ (✅)", f"{total_unique_shops - c_prob_shops}")
            st.metric("ปัญหา (⚠️/❌)", f"{c_prob_shops}")

        # แสดงตาราง Heatmap
        def apply_cell_style(val):
            if val == "✅": return 'background-color: #d4edda; color: #155724;'
            if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
            if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
            return 'color: #ced4da;'

        st.dataframe(grid_df.style.map(apply_cell_style), use_container_width=True, height=600)
    else:
        st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")

elif menu == "⚙️ Setting (ปิด-เปิดสาขา)":
    st.markdown(f"### ⚙️ ตั้งค่าการ Monitor สาขา : {selected_brand}")
    st.info("สาขาที่ 'ติ๊กถูก' จะถูกนำไปคำนวณและแจ้งเตือนในระบบ Line/Email")
    
    df_settings = get_shop_settings(selected_brand)
    
    if not df_settings.empty:
        # ใช้ Data Editor ให้ติ๊ก Checkbox ได้
        edited_df = st.data_editor(
            df_settings,
            column_config={
                "ProductLevelID": None, # ซ่อน ID
                "ProductLevelName": st.column_config.Column("ชื่อสาขา", width="large"),
                "ismonitorsales": st.column_config.CheckboxColumn("สถานะการ Monitor")
            },
            disabled=["ProductLevelName"], # แก้ชื่อไม่ได้
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("บันทึกการตั้งค่าทั้งหมด"):
            save_shop_settings(selected_brand, edited_df)
    else:
        st.write("ไม่พบข้อมูลสาขาในฐานข้อมูล")
