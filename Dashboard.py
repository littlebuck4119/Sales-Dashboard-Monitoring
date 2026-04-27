import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & STYLES ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 1.2rem !important; }
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-bottom: 0rem !important; }
    button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
    .date-card { background-color: #ffffff; padding: 20px 15px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0px 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; text-align: center; }
    .date-card .day-name { color: #ff4b4b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #1f1f1f; line-height: 1; margin: 8px 0; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
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
    except:
        return {}

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
    except:
        pass
    return pd.DataFrame()


# --- 3. HELPER: สร้าง label แบรนด์พร้อมชื่อผู้รับผิดชอบ ---
def get_brand_label(brand, monitors_config):
    """คืนค่าชื่อแบรนด์พร้อมวงเล็บชื่อ มือ1/มือ2 ถ้ามีการกำหนดไว้"""
    a = monitors_config.get(brand, {})
    parts = [x for x in [a.get("m1", ""), a.get("m2", "")] if x.strip()]
    return f"{brand} ({' / '.join(parts)})" if parts else brand


# --- 4. SIDEBAR ---
with st.sidebar:
    # --- วันที่ ---
    now = datetime.now()
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
            <div style="font-size: 0.8rem; color: #666;">📅 Today</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    # โหลด config ครั้งเดียวเพื่อดึง monitors
    current_full_config = get_config()
    monitors_config = current_full_config.get("_monitors", {})

    # --- เลือกแบรนด์ (แสดงชื่อ + วงเล็บผู้รับผิดชอบ) ---
    brand_keys = list(BRAND_CONFIG.keys())
    brand_display_options = ["🛑 SELECT BRAND 🛑"] + [
        get_brand_label(b, monitors_config) for b in brand_keys
    ]
    selected_label = st.selectbox("เลือกแบรนด์", brand_display_options, index=0)

    # แปลง label กลับเป็นชื่อ brand จริง
    if selected_label == "🛑 SELECT BRAND 🛑":
        selected_brand = "🛑 SELECT BRAND 🛑"
    else:
        # จับคู่กลับจาก label → brand key จริง
        selected_brand = brand_keys[brand_display_options.index(selected_label) - 1]

    col_y, col_m = st.columns(2)
    with col_y:
        y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month - 1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()

    st.markdown("---")

    # ─────────────────────────────────────────────────────────
    # NEW: ตั้งค่าผู้รับผิดชอบ Monitor
    # ─────────────────────────────────────────────────────────
    with st.expander("👤 กำหนดผู้รับผิดชอบ Monitor", expanded=False):
        st.caption("กำหนดชื่อผู้ Monitor มือ 1 (หลัก) และ มือ 2 (สำรอง) ต่อแบรนด์ ชื่อจะแสดงในวงเล็บหลังชื่อแบรนด์")
        st.markdown("")

        # โหลดค่าปัจจุบันจาก config (ถ้ามี)
        new_monitors = {}
        for brand in brand_keys:
            saved = monitors_config.get(brand, {})
            st.markdown(f"**{brand}**")
            c1, c2 = st.columns(2)
            with c1:
                m1_val = st.text_input(
                    "มือ 1 (หลัก)",
                    value=saved.get("m1", ""),
                    key=f"mon_m1_{brand}",
                    placeholder="ชื่อผู้รับผิดชอบ"
                )
            with c2:
                m2_val = st.text_input(
                    "มือ 2 (สำรอง)",
                    value=saved.get("m2", ""),
                    key=f"mon_m2_{brand}",
                    placeholder="ชื่อผู้รับผิดชอบ"
                )
            new_monitors[brand] = {"m1": m1_val.strip(), "m2": m2_val.strip()}

            # Preview แบบ real-time
            parts = [x for x in [m1_val.strip(), m2_val.strip()] if x]
            preview = f"{brand} ({' / '.join(parts)})" if parts else brand
            st.caption(f"📌 ตัวอย่าง: `{preview}`")
            st.markdown("---")

        if st.button("💾 บันทึกผู้รับผิดชอบ", type="primary", use_container_width=True):
            current_full_config["_monitors"] = new_monitors
            save_config(current_full_config)
            st.success("✅ บันทึกสำเร็จ!")
            st.rerun()
    # ─────────────────────────────────────────────────────────


# --- 5. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        [data-testid="stAppViewBlockContainer"] {
            padding: 0 !important;
            max-width: 100% !important;
        }
        .full-screen-welcome {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            height: 100vh;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            margin: 0;
            font-family: 'Inter', sans-serif;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 60px;
            border-radius: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            max-width: 700px;
        }
        .main-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: -2px;
            margin-bottom: 10px;
            background: linear-gradient(to right, #fff, #bdc3c7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        div.stButton > button {
            background: #4facfe !important;
            background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
            color: white !important;
            border: none !important;
            padding: 15px 40px !important;
            font-size: 1.2rem !important;
            font-weight: bold !important;
            border-radius: 50px !important;
            box-shadow: 0 10px 20px rgba(79, 172, 254, 0.4) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        div.stButton > button:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 15px 30px rgba(79, 172, 254, 0.6) !important;
        }
        </style>

        <div class="full-screen-welcome">
            <div class="glass-card">
                <div style="font-size: 5rem; margin-bottom: 20px;">📈</div>
                <h1 class="main-title">Sales Monitoring</h1>
                <p style="font-size: 1.2rem; opacity: 0.7; margin-bottom: 40px;">
                    Enterprise Performance Tracking Intelligence
                </p>
        """, unsafe_allow_html=True)
    st.stop()

st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    brand_settings = current_full_config.get(selected_brand, {})

    # --- ส่วนจัดการสาขาใน Sidebar ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):

            search_query = st_keyup(
                "🔍 ค้นหาสาขา...",
                key=f"keyup_search_{selected_brand}"
            ).strip().lower()

            master_key = f"master_{selected_brand}"

            def on_master_change():
                for s in shops:
                    st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]

            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 **เปิด/ปิด ทั้งหมด**", value=all_on, key=master_key, on_change=on_master_change)

            st.markdown("---")

            updated_settings = {
                s: st.session_state.get(f"tog_{selected_brand}_{s}", brand_settings.get(s, True))
                for s in shops
            }

            filtered_shops = [s for s in shops if search_query in s.lower()] if search_query else shops

            if not filtered_shops:
                st.info("😔 ไม่พบสาขาที่ค้นหา...")
            else:
                for shop in filtered_shops:
                    t_key = f"tog_{selected_brand}_{shop}"
                    if t_key not in st.session_state:
                        st.session_state[t_key] = brand_settings.get(shop, True)
                    updated_settings[shop] = st.toggle(f"{shop}", key=t_key)

            st.markdown("---")
            if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("บันทึกสำเร็จ!")
                st.rerun()

    # --- เตรียมโครงสร้างตาราง ---
    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    grid_df = pd.DataFrame("N/A", index=shops, columns=days)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day

        for shop in shops:
            if not brand_settings.get(shop, True):
                grid_df.loc[shop] = "DISABLED"

        for _, row in df_filtered.iterrows():
            shop = row['shop_name']
            day = row['Day']
            status = row['status_code']

            if shop in grid_df.index and grid_df.at[shop, day] != "DISABLED":
                icon = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                grid_df.at[shop, day] = icon

    # --- สรุปภาพรวม ---
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()

    with summary_placeholder.container():
        # แสดงชื่อผู้รับผิดชอบใน summary ด้วย
        monitor_info = monitors_config.get(selected_brand, {})
        m1_name = monitor_info.get("m1", "")
        m2_name = monitor_info.get("m2", "")
        if m1_name or m2_name:
            parts = [x for x in [m1_name, m2_name] if x]
            st.markdown(
                f'<div style="font-size:0.8rem; color:#555; margin-bottom:4px;">👤 Monitor: '
                f'{"&nbsp;&nbsp;|&nbsp;&nbsp;".join([f"มือ{i+1}: <b>{p}</b>" for i, p in enumerate(parts)])}'
                f'</div>',
                unsafe_allow_html=True
            )
        st.info(f"Monitor: **{len(active_shops)}** / **{len(shops)}** สาขา")
        m1, m2 = st.columns(2)
        if not active_grid.empty:
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("ปกติ ✅", len(active_shops) - prob_count)
            m2.metric("ปัญหา ⚠️/❌", prob_count)

            prob_sum = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
            if not top_prob.empty:
                st.markdown("---")
                st.write("**⚠️ สาขาที่พบปัญหาบ่อยเดือนนี้:**")
                for shop, count in top_prob.items():
                    st.markdown(
                        f'<div class="problem-item"><b>{shop}</b><br>'
                        f'<span style="color:#d32f2f; font-size:0.8rem;">พบปัญหา {int(count)} ครั้ง</span></div>',
                        unsafe_allow_html=True
                    )

    # --- Styling ---
    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;'
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(
        grid_df.style.map(apply_style),
        use_container_width=True,
        height=800,
        column_config={d: st.column_config.Column(width=35) for d in days}
    )
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")
