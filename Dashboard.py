# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import calendar
from datetime import datetime, timedelta
from st_keyup import st_keyup

# --- 1. CONFIG & STYLES ---
st.set_page_config(
    page_title="Sales Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 💡 แก้ไข CSS ให้สวิตช์ทั้ง 2 ฝั่งเมื่อเปิดใช้งาน (Checked) แสดงเป็นสีแดง และเมื่อปิดแสดงเป็นสีเทาตามบรีฟ
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
        background-color: #1e293b !important; color: white !important; border: none !important;
        border-radius: 6px !important; padding: 0.4rem 0.8rem !important;
        font-weight: 600 !important; font-size: 0.8rem !important; width: 100% !important; margin-top: 10px !important;
    }

    /* ปรับขนาดตัวอักษรในช่อง Input ของหน้า Config */
    div[data-testid="stExpander"] input { font-size: 0.9rem !important; }

    /* 🔴 ปรับคอลัมน์ที่ 2 (เปิด-ปิดร้าน) → เปิดเป็นสีแดง */
    [data-testid="stExpander"] [data-testid="column"]:nth-child(2) [data-testid="stToggle"] label:has(input:checked) > span:first-of-type {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
    }
    [data-testid="stExpander"] [data-testid="column"]:nth-child(2) input[type="checkbox"]:checked + span {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
    }

    /* 🔴 ปรับคอลัมน์ที่ 3 (เปิด-ปิดส่งยอด) → เปิดเป็นสีแดง */
    [data-testid="stExpander"] [data-testid="column"]:nth-child(3) [data-testid="stToggle"] label:has(input:checked) > span:first-of-type {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
    }
    [data-testid="stExpander"] [data-testid="column"]:nth-child(3) input[type="checkbox"]:checked + span {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
    }    
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
BRAND_CONFIG = {
    "Eat Am Are": "03018b865e46122e4d4f",
    "JonesSalad": "695d80e67b2a8c1ca2ee",
    "Laem Charoen Seafood": "98d3735c3a0a94a513f6",
    "Saemaeul/BHC/Solsot": "90a9e466a623369dfac4",
    "Tenjo": "da133cadd434914e0816",
    "Senju": "c9d33da3c6f38be07eb8",
    "Wisdom": "0ce6c62297f8f0e3405e",
    "Seefah": "41e908643e98b11931ee",
    "Bake Brother": "363e1bba0b9907b65532",
    "Ohsho": "abb1c88b8db54ca2ee87",
    "ตั่วเปา": "a8b719f0d97ea01d264c",
    "Maesriruen": "2e8f853bc23b3ba8b140",
    "You&I": "6111d22633f84f5ee575",
    "เสวย": "e7a4885887fc49db4765",
    "Shinkanzen": "5aae88055a5ff0d32c96",
    "Tudari": "ead94150854efcbfe331",
    "Spaghetti": "a1c5f81e3434b386e9b3",
    "DaddyDough": "83c8c26662e97d2a67d2",
    "DeanAndDeluca": "64ecf510fcbb2541ec33",
    "Missmamon&Taroto": "273634731d081a1230f6",
    "Lukkaithong": "131746fdd8eca1e25881",
    "Kaithong": "8cd350f18aaa86ffd8dc",
    "Shwepalin": "ee564b51ca10e448abb9",
    "CocaSuki": "95fb49a8978ca4acf1ac",
    "BaanSomtum": "71ffbd4c2491a1b2e568",
    "HormCafe": "2a34ab9d789677ee8ba2"
}
CONFIG_API = "https://api.npoint.io/9898efa2a5853bf5f886"

def get_config():
    try:
        res = requests.get(CONFIG_API, timeout=5)
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_config(full_config):
    try: requests.post(CONFIG_API, json=full_config, timeout=5)
    except: pass

@st.cache_data(ttl=30)
def get_data_from_api(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
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
    current_full_config = get_config()
    monitors_config = current_full_config.get("_monitors", {})
    
    def sort_brands_logic(b_name):
        return int(monitors_config.get(b_name, {}).get("order", 999))
        
    brand_keys = sorted(list(BRAND_CONFIG.keys()), key=sort_brands_logic)
    DEFAULT_COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]
    
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
                all_brands = list(BRAND_CONFIG.keys())
                for i, brand in enumerate(all_brands):
                    saved = monitors_config.get(brand, {})
                    cfg_color = saved.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
                    cfg_order = saved.get("order", i + 1)
                    
                    st.markdown(f"<div style='border-left:4px solid {cfg_color}; padding-left:7px; font-size:0.9rem; font-weight:700; margin-top:10px; margin-bottom:5px;'>{brand}</div>", unsafe_allow_html=True)
                    
                    c_ord, c1, c2, c3 = st.columns([0.7, 2, 2, 1])
                    with c_ord: 
                        ord_val = st.number_input("ลำดับ", value=int(cfg_order), min_value=1, step=1, key=f"mon_ord_{brand}", label_visibility="collapsed")
                    with c1: 
                        m1_val = st.text_input("มือ1", value=saved.get("m1",""), key=f"mon_m1_{brand}", label_visibility="collapsed", placeholder="มือ 1")
                    with c2: 
                        m2_val = st.text_input("มือ2", value=saved.get("m2",""), key=f"mon_m2_{brand}", label_visibility="collapsed", placeholder="มือ 2")
                    with c3: 
                        color_val = st.color_picker("Color", value=cfg_color, key=f"mon_color_{brand}", label_visibility="collapsed")
                    
                    new_monitors[brand] = {
                        "m1": m1_val.strip(), 
                        "m2": m2_val.strip(), 
                        "color": color_val,
                        "order": int(ord_val)
                    }
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 บันทึกการตั้งค่า", type="primary", use_container_width=True, key="save_brand_config"):
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
st.markdown(f"🔗 **API Source:** `https://api.npoint.io/{BRAND_CONFIG[selected_brand]}`")

full_df = get_data_from_api(f"https://api.npoint.io/{BRAND_CONFIG[selected_brand]}")

if not full_df.empty:
    # 1. แปลงคอลัมน์ให้เป็น String และเปลี่ยนพวกเลข 0 หรือ NaN ให้เป็นค่าว่างชั่วคราว
    if 'shop_code' in full_df.columns:
        full_df['shop_code'] = full_df['shop_code'].astype(str).replace(['0', '0.0', 'nan', 'None'], '')
    
    # 2. ใช้เทคนิค Map หาคู่ Shop Name กับ Shop Code ล่าสุดที่ไม่ใช่ค่าว่าง
    valid_codes = full_df[full_df['shop_code'] != ''].drop_duplicates('shop_name')
    name_to_code_map = dict(zip(valid_codes['shop_name'], valid_codes['shop_code']))
    
    # 3. เติมรหัสสาขาให้วันเก่าๆ ที่ไม่มีข้อมูลจาก Map ที่เราสร้างไว้
    full_df['final_shop_code'] = full_df['shop_name'].map(name_to_code_map).fillna('')
    
    # 4. สร้าง Label สำหรับแสดงผลในตารางและเมนูด้านข้าง
    def make_label(row):
        code = row['final_shop_code']
        name = row['shop_name']
        return f"[{code}] {name}" if code else f" {name}"
        
    full_df['display_label'] = full_df.apply(make_label, axis=1)
    
    # 💡 [แก้ไขและนิยามรายชื่อสาขาให้ลอจิกทำงานครบสมบูรณ์]
    shops = sorted(list(full_df['shop_name'].unique()))
    shops_display_dict = dict(zip(full_df['shop_name'], full_df['display_label']))
    
    brand_settings = current_full_config.get(selected_brand, {})

    with st.sidebar:
        st.markdown("---")
        # 🔗 จัดการ เปิด/ปิด / ดึงยอด สาขา
        with st.expander("🚫 จัดการ เปิด/ปิด / ดึงยอด สาขา", expanded=False):
            search_query = st_keyup("🔍 ค้นหาสาขา...", key=f"keyup_search_{selected_brand}").strip().lower()
            
            # 1. จัดทำข้อมูลเริ่มต้น
            updated_settings = {}
            for s in shops:
                old_val = brand_settings.get(s, True)
                if isinstance(old_val, dict):
                    updated_settings[s] = {
                        "active": old_val.get("active", True),
                        "sync_active": old_val.get("sync_active", old_val.get("active", True))
                    }
                else:
                    updated_settings[s] = {
                        "active": old_val,
                        "sync_active": old_val
                    }

            # 2. Callbacks สำหรับปุ่ม Master ทั้ง 2 ฝั่ง
            master_act_key = f"master_act_{selected_brand}"
            master_sync_key = f"master_sync_{selected_brand}"

            def on_master_act_change():
                m_val = st.session_state[master_act_key]
                for s in shops:
                    st.session_state[f"tog_act_{selected_brand}_{s}"] = m_val

            def on_master_sync_change():
                m_val = st.session_state[master_sync_key]
                for s in shops:
                    st.session_state[f"tog_sync_{selected_brand}_{s}"] = m_val

            # 3. คำนวณสถานะปุ่ม Master
            all_act_on = all(st.session_state.get(f"tog_act_{selected_brand}_{s}", updated_settings[s]["active"]) for s in shops)
            all_sync_on = all(st.session_state.get(f"tog_sync_{selected_brand}_{s}", updated_settings[s]["sync_active"]) for s in shops)

            # สวิตช์ เปิด/ปิด ทั้งหมด แถวเดียวคู่กัน
            col_m_name, col_m_act, col_m_sync = st.columns([1.8, 1.1, 1.1])
            with col_m_name:
                st.markdown("<div style='font-size: 0.8rem; font-weight: bold; color: #1e293b; padding-top: 4px;'>🔔 เปิด/ปิด ทั้งหมด</div>", unsafe_allow_html=True)
            with col_m_act:
                st.toggle("All Act", value=all_act_on, key=master_act_key, on_change=on_master_act_change, label_visibility="collapsed")
            with col_m_sync:
                st.toggle("All Sync", value=all_sync_on, key=master_sync_key, on_change=on_master_sync_change, label_visibility="collapsed")

            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

            # หัวตารางรายสาขา
            st.markdown("""
                <div style="display: flex; background-color: #f1f5f9; padding: 6px 4px; border-radius: 6px; margin-bottom: 8px; font-size: 0.75rem; font-weight: bold; color: #475569;">
                    <div style="flex: 1.8;">📍 รหัส & ชื่อสาขา</div>
                    <div style="flex: 1.1; text-align: center;">เปิด-ปิดร้าน</div>
                    <div style="flex: 1.1; text-align: center;">เปิด-ปิดส่งยอด</div>
                </div>
            """, unsafe_allow_html=True)

            # 4. แสดงรายการสวิตช์รายสาขา
            filtered_shops = [s for s in shops if search_query in shops_display_dict[s].lower()] if search_query else shops

            for shop in filtered_shops:
                display_shop_name = shops_display_dict[shop].replace('--', '').strip()
                
                with st.container():
                    col_name, col_act, col_sync = st.columns([1.8, 1.1, 1.1])
                    
                    with col_name:
                        st.markdown(f"<div style='font-size: 0.8rem; font-weight: 500; line-height: 1.3; padding-top: 2px; color: #1e293b; word-break: break-word;' title='{shop}'>{display_shop_name}</div>", unsafe_allow_html=True)
                    
                    with col_act:
                        t_active_key = f"tog_act_{selected_brand}_{shop}"
                        if t_active_key not in st.session_state:
                            st.session_state[t_active_key] = updated_settings[shop]["active"]
                        val_active = st.toggle("Active", key=t_active_key, label_visibility="collapsed")
                    
                    with col_sync:
                        t_sync_key = f"tog_sync_{selected_brand}_{shop}"
                        if t_sync_key not in st.session_state:
                            st.session_state[t_sync_key] = updated_settings[shop]["sync_active"]
                        val_sync = st.toggle("Sync", key=t_sync_key, label_visibility="collapsed")

                    updated_settings[shop] = {
                        "active": val_active,
                        "sync_active": val_sync
                    }
                    st.markdown("<div style='margin: 4px 0; border-bottom: 1px solid #f1f5f9;'></div>", unsafe_allow_html=True)
                    
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button("💾 บันทึกการตั้งค่าสาขา", type="primary", use_container_width=True, key="save_shops"):
                final_settings = {}
                for s in shops:
                    final_settings[s] = {
                        "active": st.session_state.get(f"tog_act_{selected_brand}_{s}", updated_settings[s]["active"]),
                        "sync_active": st.session_state.get(f"tog_sync_{selected_brand}_{s}", updated_settings[s]["sync_active"])
                    }
                
                current_full_config[selected_brand] = final_settings
                save_config(current_full_config)
                st.success("บันทึกและสแตมป์สถานะ 2 ฝั่งลง API เรียบร้อย!")
                st.rerun()
                
        if st.button("🔙 Back to Main Page", key="back_to_welcome", use_container_width=True):
            st.session_state.selected_brand = "🛑 SELECT BRAND 🛑"
            st.rerun()

    mask = (full_df['sync_date'].dt.month == m) & (full_df['sync_date'].dt.year == y)
    df_filtered = full_df[mask].copy()
    _, last_day = calendar.monthrange(y, m)
    days = list(range(1, last_day + 1))
    
    grid_index_labels = [shops_display_dict[s] for s in shops]
    grid_df = pd.DataFrame("N/A", index=grid_index_labels, columns=days)

    if not df_filtered.empty:
        df_filtered['Day'] = df_filtered['sync_date'].dt.day
        for shop in shops:
            s_cfg = brand_settings.get(shop, True)
            is_active = s_cfg.get("active", True) if isinstance(s_cfg, dict) else s_cfg
            if not is_active: 
                grid_df.loc[shops_display_dict[shop]] = "DISABLED"
        
        for _, row in df_filtered.iterrows():
            s, d = row['shop_name'], row['Day']
            display_label = shops_display_dict.get(s, s)
            
            if "⚡ Real-time" in view_mode:
                st_code = row.get('status_realtime', row.get('status_code', 0))
            else:
                st_code = row.get('status_log', row.get('status_code', 0))

            if display_label in grid_df.index and grid_df.at[display_label, d] != "DISABLED":
                grid_df.at[display_label, d] = "✅" if st_code == 2 else "⚠️" if st_code == 1 else "❌" if st_code == 0 else "N/A"

    active_shops = []
    for s in shops:
        s_cfg = brand_settings.get(s, True)
        if isinstance(s_cfg, dict):
            if s_cfg.get("active", True): active_shops.append(s)
        elif s_cfg:
            active_shops.append(s)
            
    active_grid_labels = [shops_display_dict[s] for s in active_shops]
    active_grid = grid_df.loc[active_grid_labels] if active_shops else pd.DataFrame()

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
                for shop_label, count in top_prob.items():
                    try: display_count = int(count)
                    except: display_count = 0
                        
                    st.markdown(
                        f'<div class="problem-item"><b>{shop_label}</b><br>'
                        f'<span style="color:#d32f2f; font-size:0.75rem;">พบปัญหา {display_count} ครั้ง</span></div>',
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
