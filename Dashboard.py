import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime
from st_keyup import st_keyup
from datetime import datetime, timedelta

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
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.8rem !important; }
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-bottom: 0rem !important; }
    
    button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
    .problem-item { font-size: 0.85rem; padding: 8px 10px; background-color: #fff5f5; border-left: 4px solid #ff4b4b; border-radius: 4px; margin-bottom: 6px; }
    footer { visibility: hidden; }

    /* ปรับแต่งปุ่ม Back to Main Page */
    div.stButton > button[key="back_to_welcome"] {
        background-color: #1e293b !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.8rem !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        width: 100% !important;
        margin-top: 10px !important;
    }

    /* ปรับขนาดตัวอักษรในช่อง Input ของหน้า Config */
    div[data-testid="stExpander"] input {
        font-size: 0.9rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
BRAND_CONFIG = {
    "Eat Am Are": "506e2020f13e6d515726",
    "JonesSalad": "695d80e67b2a8c1ca2ee",
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4",
    "Tenjo": "da133cadd434914e0816",
    "Senju": "c9d33da3c6f38be07eb8",
    "Wisdom": "0ce6c62297f8f0e3405e"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

def get_config():
    try:
        res = requests.get(CONFIG_API, timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_config(full_config):
    requests.post(CONFIG_API, json=full_config)

@st.cache_data(ttl=30)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                # แปลงสถานะทุกฟิลด์ให้เป็นตัวเลขเพื่อความแม่นยำ
                for col in ['status_code', 'status_log', 'status_realtime']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df['sync_date'] = pd.to_datetime(df['sync_date'])
                return df
    except: pass
    return pd.DataFrame()

# --- 3. SIDEBAR ---
with st.sidebar:
    now = datetime.utcnow() + timedelta(hours=7)
    brand_keys = list(BRAND_CONFIG.keys())
    DEFAULT_COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]

    current_full_config = get_config()
    monitors_config = current_full_config.get("_monitors", {})

    if "selected_brand" not in st.session_state:
        st.session_state.selected_brand = "🛑 SELECT BRAND 🛑"

    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button[kind="secondary"] { padding: 1px 2px !important; min-height: 32px !important; font-size: 0.6rem !important; }
        div[data-testid="stSidebar"] button[kind="primary"] {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            border: none !important; color: #f1f5f9 !important; font-size: 0.75rem !important;
            font-weight: 600 !important; border-radius: 6px !important; padding: 6px 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Date & Time card
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    padding: 12px 15px; border-radius: 12px; margin-bottom: 10px; 
                    border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase; letter-spacing: 0.5px;">📅 Today</div>
                    <div style="font-size:0.95rem; font-weight:700; color:#f8fafc;">{now.strftime("%d %b %Y")}</div>
                </div>
                <div style="text-align: right; border-left: 1px solid rgba(148, 163, 184, 0.3); padding-left: 12px;">
                    <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase; letter-spacing: 0.5px;">🕒 Time</div>
                    <div style="font-size:1.1rem; font-weight:800; color:#38bdf8;">{now.strftime("%H:%M")}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- ADDED: Mode Toggle under Date Card ---
    view_mode = st.radio(
        "Display Mode",
        ["📋 History (Log)", "⚡ Real-time"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    # --- 2. Brand selector ---
    st.markdown("<div style='font-size:0.65rem; font-weight:600; color:#64748b; text-transform:uppercase; margin-bottom:4px;'>เลือกแบรนด์</div>", unsafe_allow_html=True)

    selected_brand = st.session_state.selected_brand

    if selected_brand == "🛑 SELECT BRAND 🛑":
        display_brands = brand_keys
    else:
        display_brands = [selected_brand]

    for i, brand in enumerate(display_brands):
        original_idx = brand_keys.index(brand)
        cfg = monitors_config.get(brand, {})
        color = cfg.get("color", DEFAULT_COLORS[original_idx % len(DEFAULT_COLORS)])
        
        m1 = cfg.get("m1", "")
        m2 = cfg.get("m2", "")
        monitors_text = " / ".join([x for x in [m1, m2] if x]) or "—"
        
        is_active = (selected_brand == brand)
        bg = f"{color}25" if is_active else f"{color}10"
        border_w = "4px" if is_active else "2px"
        
        col_band, col_btn = st.columns([5, 1.2])
        with col_band:
            st.markdown(
                f'<div style="border-left:{border_w} solid {color}; background:{bg}; padding:4px 8px; border-radius:0 6px 6px 0; margin:2px 0;">'
                f'<div style="font-size:0.9rem; font-weight:{"700" if is_active else "500"}; color:{"#0f172a" if is_active else "#475569"}; line-height:1.2;">{brand}</div>'
                f'<div style="font-size:0.75rem; color:{color}; font-weight:600;">{monitors_text}</div>'
                f'</div>', unsafe_allow_html=True
            )
        with col_btn:
            btn_label = "▶" if selected_brand == "🛑 SELECT BRAND 🛑" else "🔄"
            if st.button(btn_label, key=f"brand_btn_{brand}", use_container_width=True):
                st.session_state.selected_brand = brand
                st.rerun()

    selected_brand = st.session_state.selected_brand

    # 3. ปี / เดือน
    st.markdown("<div style='margin-top:5px'></div>", unsafe_allow_html=True)
    col_y, col_m = st.columns(2)
    with col_y:
        y = st.selectbox("ปี", [2025, 2026], index=1, key="sb_year")
    with col_m:
        month_list = list(calendar.month_name)[1:]
        m_name = st.selectbox("เดือน", month_list, index=now.month - 1, key="sb_month")
        m = month_list.index(m_name) + 1

    summary_placeholder = st.empty()
    st.markdown("<hr style='border:none; border-top:1px solid #e2e8f0; margin:8px 0;'>", unsafe_allow_html=True)

    # ── 4. Settings ──
    if selected_brand == "🛑 SELECT BRAND 🛑":
        with st.expander("👤 User Configuration", expanded=False):
            pwd = st.text_input("กรอกรหัสผ่านเพื่อแก้ไข", type="password", key="admin_pwd")
            if pwd == "SYN1234":
                st.success("Login Success")
                new_monitors = {}
                for i, brand in enumerate(brand_keys):
                    saved = monitors_config.get(brand, {})
                    cfg_color = saved.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
                    st.markdown(f"<div style='border-left:4px solid {cfg_color}; padding-left:7px; font-size:0.9rem; font-weight:700; margin-top:10px; margin-bottom:5px;'>{brand}</div>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1: m1_val = st.text_input("มือ1", value=saved.get("m1",""), key=f"mon_m1_{brand}", label_visibility="collapsed", placeholder="มือ 1")
                    with c2: m2_val = st.text_input("มือ2", value=saved.get("m2",""), key=f"mon_m2_{brand}", label_visibility="collapsed", placeholder="มือ 2")
                    with c3: color_val = st.color_picker("Color", value=cfg_color, key=f"mon_color_{brand}", label_visibility="collapsed")
                    new_monitors[brand] = {"m1": m1_val.strip(), "m2": m2_val.strip(), "color": color_val}
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True):
                    current_full_config["_monitors"] = new_monitors
                    save_config(current_full_config)
                    st.success("บันทึกสำเร็จ!")
                    st.rerun()
            elif pwd != "":
                st.error("รหัสผ่านไม่ถูกต้อง")

# --- 4. MAIN CONTENT ---
if selected_brand == "🛑 SELECT BRAND 🛑":
    st.markdown("""
        <style>
        [data-testid="stAppViewBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
        .full-screen-welcome {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            height: 100vh; width: 100%; display: flex; flex-direction: column;
            justify-content: center; align-items: center; color: white; text-align: center;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1); padding: 60px; border-radius: 40px;
        }
        </style>
        <div class="full-screen-welcome">
            <div class="glass-card">
                <div style="font-size: 5rem; margin-bottom: 20px;">📈</div>
                <h1 style="font-size: 4rem; font-weight: 800;">Sales Monitoring System</h1>
                <p style="font-size: 1.2rem; opacity: 0.7;">History&Realtime Tracking Dashboard</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD VIEW ---
header_mode_suffix = "(Real-time)" if "⚡ Real-time" in view_mode else "(History Log)"
st.markdown(f"### 📊 Sales Monitoring Heatmap : {selected_brand} <small style='color:#666; font-size:14px;'>{header_mode_suffix}</small>", unsafe_allow_html=True)
full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    shops = sorted(full_df['shop_name'].unique())
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        with st.expander("🚫 จัดการ เปิด/ปิด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"keyup_search_{selected_brand}").strip().lower()
            master_key = f"master_{selected_brand}"
            def on_master_change():
                for s in shops: st.session_state[f"tog_{selected_brand}_{s}"] = st.session_state[master_key]
            
            all_on = all(brand_settings.get(s, True) for s in shops)
            st.toggle("🔔 **เปิด/ปิด ทั้งหมด**", value=all_on, key=master_key, on_change=on_master_change)

            updated_settings = {s: st.session_state.get(f"tog_{selected_brand}_{s}", brand_settings.get(s, True)) for s in shops}
            filtered_shops = [s for s in shops if search_query in s.lower()] if search_query else shops

            for shop in filtered_shops:
                t_key = f"tog_{selected_brand}_{shop}"
                if t_key not in st.session_state: st.session_state[t_key] = brand_settings.get(shop, True)
                updated_settings[shop] = st.toggle(f"{shop}", key=t_key)

            if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True, key="save_shops"):
                current_full_config[selected_brand] = updated_settings
                save_config(current_full_config)
                st.success("บันทึกสำเร็จ!")
                st.rerun()
        
        if st.button("🔙 Back to Main Page", key="back_to_welcome", use_container_width=True):
            st.session_state.selected_brand = "🛑 SELECT BRAND 🛑"
            st.rerun()

    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    grid_df = pd.DataFrame("N/A", index=shops, columns=days)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in shops:
            if not brand_settings.get(shop, True): grid_df.loc[shop] = "DISABLED"
        
        for _, row in df_filtered.iterrows():
            s, d = row['shop_name'], row['Day']
            
            # --- เลือกสถานะตามโหมดที่เลือก (Fallback ไปที่ status_code ถ้าไม่มีฟิลด์ใหม่) ---
            if "⚡ Real-time" in view_mode:
                st_code = row.get('status_realtime', row.get('status_code', 0))
            else:
                st_code = row.get('status_log', row.get('status_code', 0))

            if s in grid_df.index and grid_df.at[s, d] != "DISABLED":
                grid_df.at[s, d] = "✅" if st_code == 2 else "⚠️" if st_code == 1 else "❌" if st_code == 0 else "N/A"

    active_shops = [s for s in shops if brand_settings.get(s, True)]
    active_grid = grid_df.loc[active_shops] if active_shops else pd.DataFrame()

    with summary_placeholder.container():
        monitor_info = monitors_config.get(selected_brand, {})
        m1_n, m2_n = monitor_info.get("m1", ""), monitor_info.get("m2", "")
        if m1_n or m2_n:
            parts = [f"มือ{i+1}: <b>{p}</b>" for i, p in enumerate([x for x in [m1_n, m2_n] if x])]
            st.markdown(f'<div style="font-size:0.75rem; color:#555; margin-bottom:4px;">👤 Monitor: {" | ".join(parts)}</div>', unsafe_allow_html=True)
        
        st.info(f"Monitor: **{len(active_shops)}** / **{len(shops)}** สาขา")
        if not active_grid.empty:
            prob_count = active_grid.isin(["⚠️", "❌"]).any(axis=1).sum()
            col1, col2 = st.columns(2)
            col1.metric("ปกติ ✅", len(active_shops) - prob_count)
            col2.metric("ปัญหา ⚠️/❌", prob_count)

            prob_sum = (active_grid == "❌").sum(axis=1) + (active_grid == "⚠️").sum(axis=1)
            top_prob = prob_sum[prob_sum > 0].sort_values(ascending=False).head(3)
            if not top_prob.empty:
                st.markdown("---")
                st.write("**⚠️ สาขาที่พบปัญหาบ่อยเดือนนี้:**")
                for shop, count in top_prob.items():
                    st.markdown(
                        f'<div class="problem-item"><b>{shop}</b><br>'
                        f'<span style="color:#d32f2f; font-size:0.75rem;">พบปัญหา {int(count)} ครั้ง</span></div>',
                        unsafe_allow_html=True
                    )

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
