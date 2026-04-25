import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup

# --- 1. CONFIG & STYLES ---
# ดึง sidebar state จาก session_state (ถ้ากดปุ่มจะเป็น expanded)
_sidebar_state = st.session_state.get("sidebar_state", "collapsed")

st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state=_sidebar_state
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
    except: return {}

def save_config(full_config):
    requests.post(CONFIG_API, json=full_config)

@st.cache_data(ttl=30) # ลดเวลา Cache ลงหน่อยให้พี่เติ้ลเห็นผลไวขึ้น
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


# --- 1. เตรียมพื้นที่ด้านบนสุดของ Sidebar (เพื่อให้โชว์ตลอดเวลา) ---
with st.sidebar:
    # ส่วนวันที่ (ใส่ไว้บนสุดเลยครับ)
    now = datetime.now()
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
            <div style="font-size: 0.8rem; color: #666;">📅 Today</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{now.strftime("%A, %d %b %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

    # เลือกแบรนด์
    brand_options = ["🛑 SELECT BRAND 🛑"] + list(BRAND_CONFIG.keys())
    selected_brand = st.selectbox("เลือกแบรนด์", brand_options, index=0)
    
    col_y, col_m = st.columns(2)
    with col_y: y = st.selectbox("ปี", [2025, 2026], index=1)
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month-1)
        m = month_list.index(m_name) + 1

    # จองพื้นที่สรุปผลไว้ (ป้องกัน NameError ในอนาคต)
    summary_placeholder = st.empty()
    
    

# --- 4. MAIN CONTENT (หน้าขวาตอนยังไม่เลือกแบรนด์) ---

if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

        /* โปะ background ทุก layer ของ main content — sidebar ไม่โดน */
        .stApp {
            background-color: #080e1c !important;
        }
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        [data-testid="stMain"] {
            background: linear-gradient(145deg, #080e1c 0%, #0b1a33 45%, #0d2244 100%) !important;
            min-height: 100vh !important;
        }
        [data-testid="stMain"] > div,
        [data-testid="stMain"] .block-container {
            background: transparent !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        .welcome-wrapper {
            min-height: calc(100vh - 60px);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem 1rem;
            font-family: 'DM Sans', sans-serif;
        }

        .welcome-hero {
            position: relative;
            background: linear-gradient(145deg, #080e1c 0%, #0b1a33 45%, #0d2244 100%);
            border-radius: 28px;
            padding: 56px 64px 48px;
            max-width: 760px;
            width: 100%;
            text-align: center;
            border: 1px solid rgba(99, 179, 237, 0.12);
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.03),
                0 32px 72px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.06);
            overflow: hidden;
        }

        .welcome-hero::before {
            content: '';
            position: absolute;
            top: -100px; left: -80px;
            width: 320px; height: 320px;
            background: radial-gradient(circle, rgba(56, 182, 255, 0.12) 0%, transparent 70%);
            pointer-events: none;
        }
        .welcome-hero::after {
            content: '';
            position: absolute;
            bottom: -80px; right: -60px;
            width: 280px; height: 280px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.10) 0%, transparent 70%);
            pointer-events: none;
        }

        .welcome-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(56, 182, 255, 0.08);
            border: 1px solid rgba(56, 182, 255, 0.2);
            border-radius: 100px;
            padding: 5px 18px;
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #7dd3fc;
            margin-bottom: 28px;
        }

        .welcome-title {
            font-family: 'Syne', sans-serif;
            font-size: 3.2rem;
            font-weight: 800;
            letter-spacing: -1.5px;
            line-height: 1.06;
            margin: 0 0 14px 0;
            background: linear-gradient(130deg, #ffffff 20%, #93c5fd 65%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .welcome-subtitle {
            font-size: 0.98rem;
            font-weight: 300;
            color: rgba(255,255,255,0.38);
            margin-bottom: 44px;
            line-height: 1.7;
        }

        .welcome-stats {
            display: flex;
            justify-content: center;
            gap: 0;
            margin-bottom: 44px;
            padding: 24px 0;
            border-top: 1px solid rgba(255,255,255,0.05);
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .stat-item {
            flex: 1;
            text-align: center;
            padding: 0 8px;
        }
        .stat-item + .stat-item {
            border-left: 1px solid rgba(255,255,255,0.06);
        }
        .stat-number {
            font-family: 'Syne', sans-serif;
            font-size: 1.9rem;
            font-weight: 700;
            color: #fff;
            line-height: 1;
        }
        .stat-label {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.3);
            margin-top: 5px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .welcome-hint {
            font-size: 0.78rem;
            color: rgba(255,255,255,0.2);
            margin-top: 18px;
            letter-spacing: 0.3px;
            font-style: italic;
        }

        .welcome-btn-container {
            display: flex;
            justify-content: center;
        }
        .js-open-sidebar {
            background: linear-gradient(135deg, #2563eb 0%, #6366f1 100%);
            color: white;
            border: none;
            padding: 14px 44px;
            font-size: 0.95rem;
            font-weight: 600;
            font-family: 'DM Sans', sans-serif;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
            letter-spacing: 0.4px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .js-open-sidebar:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(99, 102, 241, 0.5);
        }
        .js-open-sidebar:active {
            transform: translateY(0px);
        }

        .brand-chips {
            display: flex;
            gap: 8px;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 40px;
        }
        .brand-chip {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.45);
            letter-spacing: 0.3px;
        }
        </style>

        <div class="welcome-wrapper">
            <div class="welcome-hero">
                <div class="welcome-badge">📊 &nbsp; Real-time Intelligence</div>
                <h1 class="welcome-title">Sales Monitoring<br>Dashboard</h1>
                <p class="welcome-subtitle">
                    ระบบติดตามยอดขายและสถานะการ Sync ข้อมูลแบบ Real-time<br>
                    ครอบคลุมทุกสาขา ทุกแบรนด์ในเครือ
                </p>
                <div class="brand-chips">
                    <div class="brand-chip">🍽️ Eat Am Are</div>
                    <div class="brand-chip">🥗 JonesSalad</div>
                    <div class="brand-chip">🦞 Laem Charoen Seafood</div>
                    <div class="brand-chip">🍗 Saemaeul / BHC / Solsot</div>
                </div>
                <div class="welcome-stats">
                    <div class="stat-item">
                        <div class="stat-number">4</div>
                        <div class="stat-label">Brands</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" style="color: #7dd3fc; font-size: 1.2rem; padding-top: 4px;">Real-time</div>
                        <div class="stat-label">Data Sync</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" style="color: #c4b5fd;">30s</div>
                        <div class="stat-label">Cache TTL</div>
                    </div>
                </div>
        """, unsafe_allow_html=True)

    # JS คลิก sidebar toggle button โดยตรง — ทำงานได้ทันทีโดยไม่ต้อง rerun
    st.markdown('''
    <div class="welcome-btn-container">
        <button class="js-open-sidebar" onclick="openSidebar()">เริ่มต้นใช้งาน →</button>
    </div>
    <script>
    function openSidebar() {
        // หา sidebar toggle button ของ Streamlit แล้วคลิก
        const tryClick = () => {
            // Streamlit sidebar collapse button selectors (รองรับหลาย version)
            const selectors = [
                'button[data-testid="collapsedControl"]',
                'button[kind="header"][aria-label*="sidebar"]',
                '[data-testid="stSidebarCollapsedControl"] button',
                'section[data-testid="stSidebar"] + div button',
            ];
            for (const sel of selectors) {
                const btn = window.parent.document.querySelector(sel);
                if (btn) { btn.click(); return true; }
            }
            return false;
        };

        if (!tryClick()) {
            // ถ้ายังหาไม่เจอ ลองใหม่อีกครั้ง
            setTimeout(tryClick, 300);
        }
    }
    </script>
    ''', unsafe_allow_html=True)

    st.markdown("""
                <p class="welcome-hint">← เลือกแบรนด์จาก Sidebar ด้านซ้ายเพื่อเริ่มต้น</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand}")
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    current_full_config = get_config()
    brand_settings = current_full_config.get(selected_brand, {})


  # --- ส่วนจัดการสาขาใน Sidebar ---
    with st.sidebar:
        st.markdown("---")
        # ใส่ข้อความใน "" ให้ชัดเจนครับพี่ มันจะได้โชว์บนหัว Expander
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            
            # 1. พิมพ์ค้นหา (KeyUp)
            from st_keyup import st_keyup
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
            
            # ดึงค่า Config ปัจจุบัน
            updated_settings = {s: st.session_state.get(f"tog_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}

            # กรองรายชื่อสาขา
            filtered_shops = [s for s in shops if search_query in s.lower()] if search_query else shops

            # ส่วนการแสดงผล Toggle
            if not filtered_shops:
                st.info("😔 ไม่พบสาขาที่ค้นหา...")
            else:
                for shop in filtered_shops:
                    t_key = f"tog_{selected_brand}_{shop}"
                    if t_key not in st.session_state:
                        st.session_state[t_key] = brand_settings.get(shop, True)
                    
                    # บันทึกสถานะลงตัวแปร updated_settings ทันที
                    updated_settings[shop] = st.toggle(f"{shop}", key=t_key)
            
            st.markdown("---")
            # ปุ่มบันทึกข้อมูล
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

    # --- จุดแก้ไขสำคัญ: วนลูปหยอดข้อมูลให้ตรงช่อง ---
    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        
        # 1. จัดการสาขาที่ถูก DISABLED (เทาทั้งแถว)
        for shop in shops:
            if not brand_settings.get(shop, True):
                grid_df.loc[shop] = "DISABLED"

        # 2. เอาข้อมูลจริงมาหยอดลงช่อง (ถ้าไม่ได้ DISABLED)
        for _, row in df_filtered.iterrows():
            shop = row['shop_name']
            day = row['Day']
            status = row['status_code']
            
            if shop in grid_df.index and grid_df.at[shop, day] != "DISABLED":
                # ใส่ไอคอนตาม status_code จริงจาก API
                icon = "✅" if status == 2 else "⚠️" if status == 1 else "❌" if status == 0 else "N/A"
                grid_df.at[shop, day] = icon

    # --- สรุปภาพรวม (Summary) ---
    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()
    
    with summary_placeholder.container():
        st.info(f"Monitor: **{len(active_shops)}** / **{len(shops)}** สาขา")
        m1, m2 = st.columns(2)
        if not active_grid.empty:
            # เช็คว่าแถวไหนมี ⚠️ หรือ ❌ บ้าง
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            m1.metric("ปกติ ✅", len(active_shops) - prob_count)
            m2.metric("ปัญหา ⚠️/❌", prob_count)
            
            prob_sum = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
            if not top_prob.empty:
                st.markdown("---")
                st.write("**⚠️ สาขาที่พบปัญหาบ่อยเดือนนี้:**")
                for shop, count in top_prob.items():
                    st.markdown(f'<div class="problem-item"><b>{shop}</b><br><span style="color:#d32f2f; font-size:0.8rem;">พบปัญหา {int(count)} ครั้ง</span></div>', unsafe_allow_html=True)

    # --- การระบายสี (Styling) ---
    def apply_style(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724;'
        if val == "⚠️": return 'background-color: #fff3cd; color: #856404;'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24;'
        if val == "DISABLED": return 'background-color: #6c757d; color: transparent;' 
        return 'color: #ced4da; font-size: 10px;'

    st.dataframe(grid_df.style.map(apply_style), use_container_width=True, height=800, 
                 column_config={d: st.column_config.Column(width=35) for d in days})
else:
    st.warning("⚠️ ไม่พบข้อมูลสำหรับแบรนด์นี้")
