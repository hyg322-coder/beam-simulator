import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# ページ設定
st.set_page_config(page_title="大梁断面算定シミュレーター", layout="wide")

# 見出しを携帯向けに小さく調整
st.markdown("## 🏗️ 大梁断面算定シミュレーター")

# --- 1. データベース ---
material_db = {
    "杉 (E70)": {"E": 7000, "fb": 10.0, "fs": 0.8},
    "桧 (E90)": {"E": 9000, "fb": 11.3, "fs": 1.0},
    "米松 (E110)": {"E": 11000, "fb": 13.3, "fs": 1.2},
    "集成材 (E120)": {"E": 12000, "fb": 14.6, "fs": 1.3},
    "任意入力": {"E": 7000, "fb": 10.0, "fs": 0.8}
}

# --- 2. サイドバー設定 ---
st.sidebar.header("1. 荷重条件")
mode = st.sidebar.radio("荷重タイプ", ("等分布荷重 (全体)", "集中荷重 (中央)"))

st.sidebar.markdown("---")
st.sidebar.header("2. 材料・断面")
selected_label = st.sidebar.selectbox("樹種選択", list(material_db.keys()))

if selected_label == "任意入力":
    E = st.sidebar.number_input("E", value=7000)
    fb = st.sidebar.number_input("fb", value=10.0)
    fs = st.sidebar.number_input("fs", value=0.8)
else:
    E, fb, fs = material_db[selected_label]["E"], material_db[selected_label]["fb"], material_db[selected_label]["fs"]

L = st.sidebar.select_slider("L (mm)", options=list(range(910, 6001, 455)), value=3640)
b = st.sidebar.select_slider("b (mm)", options=[105, 120, 150, 180, 210, 240, 270], value=120)
h = st.sidebar.select_slider("h (mm)", options=[105, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510], value=240)

# --- 3. 計算ロジック ---
Z, A, I = (b * h**2) / 6, b * h, (b * h**3) / 12
x_vals = np.linspace(0, L, 100)

if mode == "等分布荷重 (全体)":
    w = st.sidebar.number_input("w (N/mm)", value=5.0)
    M_max, Q_max = (w * L**2) / 8, (w * L) / 2
    m_diag = (w * x_vals / 2) * (L - x_vals)
    s_diag = (w * L / 2) - (w * x_vals)
    delta_max = (5 * w * (L**4)) / (384 * E * I)
    def get_delta(x):
        return (w * x * (L**3 - 2*L*(x**2) + (x**3))) / (24 * E * I)
else:
    P = st.sidebar.number_input("P (N)", value=18200.0)
    M_max, Q_max = (P * L) / 4, P / 2
    m_diag = np.where(x_vals < L/2, (P * x_vals)/2, (P * (L - x_vals))/2)
    s_diag = np.where(x_vals < L/2, P/2, -P/2)
    delta_max = (P * (L**3)) / (48 * E * I)
    def get_delta(x):
        return (P * x * (3*(L**2) - 4*(x**2))) / (48 * E * I) if x <= L/2 else (P * (L-x) * (3*(L**2) - 4*((L-x)**2))) / (48 * E * I)

sigma_b, tau = M_max / Z, (1.5 * Q_max) / A
ratio = int(L / delta_max) if delta_max > 0 else 0

# --- 4. 断面算定結果 (モバイル究極スリム表示) ---
st.subheader("📋 断面算定結果")

def compact_result_card(label, val_text, limit_val, is_ok):
    color = "#28a745" if is_ok else "#dc3545"
    bg_color = "#e9f7ef" if is_ok else "#fdecea"
    status = "OK" if is_ok else "NG"
    st.markdown(f"""
        <div style="background-color: {bg_color}; border-radius: 6px; padding: 6px 12px; border: 1px solid {color}; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
            <div style="flex-grow: 1;">
                <div style="font-size: 11px; color: #555; font-weight: bold; margin-bottom: 1px;">{label}</div>
                <div style="display: flex; align-items: baseline; gap: 8px;">
                    <span style="font-size: 17px; font-weight: 800; color: #000;">{val_text}</span>
                    <span style="font-size: 13px; color: #666; font-weight: bold;">≦ {limit_val}</span>
                </div>
            </div>
            <div style="font-size: 28px; font-weight: 900; color: {color}; line-height: 1; padding-left: 10px;">{status}</div>
        </div>
    """, unsafe_allow_html=True)

compact_result_card("曲げ(M): σb", f"{sigma_b:.2f} N/mm²", f"{fb:.1f}", sigma_b <= fb)
compact_result_card("せん断(S): τ", f"{tau:.2f} N/mm²", f"{fs:.1f}", tau <= fs)
compact_result_card("たわみ(d): δ", f"{delta_max:.2f} mm", f"{L/300:.
