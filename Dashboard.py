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
    /* ===== IMPORT FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    /* ===== GLOBAL RESET & BACKGROUND ===== */
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }
    [data-testid="stApp"] {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 30%, #1a1040 60%, #0a1628 100%) !important;
    }
    /* เพิ่ม animated mesh gradient ข้างหลัง */
    [data-testid="stApp"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse 80% 50% at 20% 20%, rgba(99,102,241,0.15) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 80%, rgba(16,185,129,0.12) 0%, transparent 60%),
            radial-gradient(ellipse 50% 60% at 60% 10%, rgba(245,158,11,0.07) 0%, transparent 60%);
        pointer-events: none;
        z-index: 0;
    }

    /* ===== BLOCK CONTAINER ===== */
    .block-container {
        padding-top: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-bottom: 0rem !important;
        position: relative;
        z-index: 1;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 26, 0.92) !important;
        border-right: 1px solid rgba(99,102,241,0.25) !important;
        backdrop-filter: blur(20px) !important;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 1rem !important;
    }

    /* ===== TYPOGRAPHY ===== */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
        color: #e2e8f0 !important;
    }
    h1, h2, h3, .main-title {
        font-family: 'Syne', sans-serif !important;
    }

    /* ===== SIDEBAR TOGGLE BUTTON ===== */
    .sidebar-toggle-btn {
        position: fixed;
        top: 50%;
        left: 0;
        transform: translateY(-50%);
        z-index: 9999;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 0 12px 12px 0;
        width: 28px;
        height: 80px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 4px 0 20px rgba(99,102,241,0.4);
        transition: all 0.3s ease;
        writing-mode: vertical-rl;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 2px;
        color: white;
        text-transform: uppercase;
    }
    .sidebar-toggle-btn:hover {
        width: 36px;
        box-shadow: 6px 0 30px rgba(99,102,241,0.6);
    }

    /* ===== METRIC & CARD STYLES ===== */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
    }

    /* ===== DATAFRAME ===== */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        box-shadow: 0 4px 40px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stDataFrame"] iframe {
        border-radius: 16px !important;
    }

    /* ===== SELECTBOX & INPUTS ===== */
    [data-testid="stSelectbox"] > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
    }

    /* ===== PRIMARY BUTTON ===== */
    button[kind="primary"],
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 6px 25px rgba(99,102,241,0.55) !important;
        transform: translateY(-1px) !important;
    }

    /* ===== WELCOME PAGE BUTTON ===== */
    .welcome-page div.stButton > button {
        background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 50px !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        box-shadow: 0 10px 30px rgba(79,172,254,0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .welcome-page div.stButton > button:hover {
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 15px 40px rgba(79,172,254,0.6) !important;
    }

    /* ===== DATE CARD ===== */
    .date-card {
        background: rgba(255,255,255,0.05);
        padding: 20px 15px;
        border-radius: 12px;
        border: 1px solid rgba(99,102,241,0.25);
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
        margin-bottom: 10px;
        text-align: center;
    }
    .date-card .day-name { color: #f59e0b; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
    .date-card .date-number { font-size: 2.2rem; font-weight: 800; color: #e2e8f0; line-height: 1; margin: 8px 0; }

    /* ===== PROBLEM ITEM ===== */
    .problem-item {
        font-size: 0.85rem;
        padding: 8px 10px;
        background: rgba(239,68,68,0.1);
        border-left: 3px solid #ef4444;
        border-radius: 6px;
        margin-bottom: 6px;
        color: #fca5a5;
    }

    /* ===== EXPANDER ===== */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
    }

    /* ===== TITLE AREA ===== */
    .dashboard-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        color: #e2e8f0;
        padding: 10px 0 6px 0;
        border-bottom: 2px solid rgba(99,102,241,0.3);
        margin-bottom: 16px;
        background: linear-gradient(to right, #a5b4fc, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

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


# --- 3. SIDEBAR ---
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
        <div style="background: rgba(99,102,241,0.12); padding: 12px 14px; border-radius: 12px;
                    border-left: 4px solid #6366f1; margin-bottom: 16px;">
            <div style="font-size: 0.75rem; color: #a5b4fc; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">📅 Today</div>
            <div style="font-size: 1rem; font-weight: 700; color: #e2e8f0; margin-top: 4px;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)

    col_y, col_m = st.columns(2)
    with col_y:
        y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month - 1)
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()


# --- 4. SIDEBAR TOGGLE BUTTON (fixed, always visible) ---
st.markdown("""
    <button class="sidebar-toggle-btn" onclick="
        const sidebar = window.parent.document.querySelector('[data-testid=stSidebar]');
        const btn = window.parent.document.querySelector('[data-testid=collapsedControl]') ||
                    window.parent.document.querySelector('button[aria-label*=sidebar]') ||
                    window.parent.document.querySelector('button[aria-label*=Sidebar]');
        if(btn) btn.click();
    " title="Toggle Sidebar">
        ☰
    </button>
""", unsafe_allow_html=True)


# --- 5. WELCOME PAGE ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        /* ล้าง padding สำหรับหน้า welcome */
        [data-testid="stAppViewBlockContainer"] {
            padding: 0 !important;
            max-width: 100% !important;
        }
        </style>

        <div style="
            min-height: 100vh;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 40px 20px;
        ">
            <div style="
                background: rgba(255,255,255,0.04);
                backdrop-filter: blur(30px);
                border: 1px solid rgba(255,255,255,0.08);
                padding: 70px 60px;
                border-radius: 32px;
                box-shadow: 0 30px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
                max-width: 680px;
                width: 100%;
            ">
                <!-- Animated icon -->
                <div style="
                    font-size: 4.5rem;
                    margin-bottom: 24px;
                    display: inline-block;
                    filter: drop-shadow(0 0 30px rgba(99,102,241,0.6));
                    animation: float 3s ease-in-out infinite;
                ">📈</div>

                <h1 style="
                    font-family: 'Syne', sans-serif;
                    font-size: 3.2rem;
                    font-weight: 800;
                    letter-spacing: -2px;
                    margin: 0 0 12px 0;
                    background: linear-gradient(135deg, #a5b4fc 0%, #e2e8f0 50%, #6ee7b7 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                ">Sales Monitoring</h1>

                <p style="
                    font-size: 1rem;
                    color: rgba(226,232,240,0.5);
                    margin-bottom: 20px;
                    letter-spacing: 0.5px;
                ">Enterprise Performance Tracking Intelligence</p>

                <!-- Divider -->
                <div style="
                    width: 60px; height: 3px;
                    background: linear-gradient(to right, #6366f1, #8b5cf6);
                    border-radius: 2px;
                    margin: 0 auto 36px auto;
                "></div>

                <!-- Stats chips -->
                <div style="display: flex; gap: 12px; justify-content: center; margin-bottom: 40px; flex-wrap: wrap;">
                    <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 20px; padding: 6px 16px; font-size: 0.8rem; color: #a5b4fc;">4 Brands</div>
                    <div style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px; padding: 6px 16px; font-size: 0.8rem; color: #6ee7b7;">Real-time Sync</div>
                    <div style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3); border-radius: 20px; padding: 6px 16px; font-size: 0.8rem; color: #fcd34d;">Daily Heatmap</div>
                </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="welcome-page">', unsafe_allow_html=True)
    if st.button("🚀 GET STARTED — Open Control Panel"):
        st.session_state.sidebar_state = 'expanded'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
                <p style="margin-top: 24px; font-size: 0.8rem; color: rgba(226,232,240,0.3); letter-spacing: 1px;">
                    ← Click the button or use the purple tab on the left
                </p>
            </div>
        </div>

        <style>
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-12px); }
        }
        </style>
    """, unsafe_allow_html=True)
    st.stop()


# --- 6. MAIN DASHBOARD ---
st.markdown(f'<div class="dashboard-title">📊 Sales Monitoring Heatmap · {selected_brand}</div>', unsafe_allow_html=True)

full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})

    # --- Sidebar: Branch Management ---
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

    # --- Build Grid ---
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

    # --- Summary ---
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()

    with summary_placeholder.container():
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
                        f'<span style="font-size:0.8rem;">พบปัญหา {int(count)} ครั้ง</span></div>',
                        unsafe_allow_html=True
                    )

    # --- Styling ---
    def apply_style(val):
        if val == "✅": return 'background-color: #052e16; color: #4ade80; text-align: center;'
        if val == "⚠️": return 'background-color: #451a03; color: #fbbf24; text-align: center;'
        if val == "❌": return 'background-color: #3b0764; color: #f87171; text-align: center;'
        if val == "DISABLED": return 'background-color: #1e293b; color: transparent;'
        return 'color: #334155; font-size: 10px; text-align: center;'

    st.dataframe(
        grid_df.style.map(apply_style),
        use_container_width=True,
        height=800,
        column_config={d: st.column_config.Column(width=35) for d in days}
    )
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")
