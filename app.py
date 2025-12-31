import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# ページ設定
st.set_page_config(page_title="大梁断面算定シミュレーター", layout="wide")

st.title("🏗️ 大梁断面算定シミュレーター")

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
    E = st.sidebar.number_input("E (N/mm²)", value=7000)
    fb = st.sidebar.number_input("fb (N/mm²)", value=10.0)
    fs = st.sidebar.number_input("fs (N/mm²)", value=0.8)
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

# --- 4. 断面算定結果 (巨大OKカード) ---
def result_card(label, value, limit, is_ok):
    color = "#28a745" if is_ok else "#dc3545"
    bg_color = "#d4edda" if is_ok else "#f8d7da"
    text_color = "#155724" if is_ok else "#721c24"
    status = "OK" if is_ok else "NG"
    st.markdown(f"""
        <div style="background-color: {bg_color}; border-radius: 10px; padding: 20px; text-align: center; border: 2px solid {color}; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 16px; color: {text_color}; font-weight: bold;">{label}</p>
            <h2 style="margin: 10px 0; color: {text_color}; font-size: 28px;">{value}</h2>
            <h1 style="margin: 0; font-size: 56px; color: {color}; font-weight: 900; line-height: 1.2;">{status}</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: {text_color}; opacity: 0.8;">{limit}</p>
        </div>
    """, unsafe_allow_html=True)

st.subheader("📋 断面算定結果")
c1, c2, c3 = st.columns(3)
with c1:
    result_card("曲げ応力度検定", f"{sigma_b:.2f} N/mm²", f"(≦{fb:.1f})", sigma_b <= fb)
with c2:
    result_card("せん断応力度検定", f"{tau:.2f} N/mm²", f"(≦{fs:.1f})", tau <= fs)
with c3:
    result_card("撓み検定", f"{delta_max:.2f} mm", f"(1/{ratio})", delta_max <= L/300)

# --- 5. グラフ描画 ---
st.markdown("### 📊 応力・変形図")

fig, (ax_m, ax_s, ax_d) = plt.subplots(3, 1, figsize=(10, 9.5))
plt.subplots_adjust(hspace=0.6)

# M図: 20固定
ax_m.xaxis.set_major_locator(ticker.MultipleLocator(455))
ax_m.grid(True, linestyle="--", alpha=0.3)
ax_m.plot([0, L], [0, 0], 'k-', linewidth=1.5)
ax_m.plot(0, 0, '^k', markersize=10)
ax_m.plot(L, 0, '^k', markersize=10)
ax_m.set_title("M (kN-m)", loc='left', fontsize=12, fontweight='bold')
ax_m.set_xlim(-150, L + 150)
ax_m.fill_between(x_vals, m_diag/1e6, 0, color="green", alpha=0.15)
ax_m.plot(x_vals, m_diag/1e6, color="forestgreen", linewidth=3.0)
ax_m.set_ylim(20, -5) 
ax_m.text(L/2, (M_max/1e6) + 0.3, f"M={M_max/1e6:.2f}\n(σb={sigma_b:.2f})", color="forestgreen", ha="center", va="bottom", fontsize=10, fontweight='bold')

# S図: 20固定・右下がり
ax_s.xaxis.set_major_locator(ticker.MultipleLocator(455))
ax_s.grid(True, linestyle="--", alpha=0.3)
ax_s.plot([0, L], [0, 0], 'k-', linewidth=1.5)
ax_s.plot(0, 0, '^k', markersize=10)
ax_s.plot(L, 0, '^k', markersize=10)
ax_s.set_title("S (kN)", loc='left', fontsize=12, fontweight='bold')
ax_s.set_xlim(-150, L + 150)
ax_s.fill_between(x_vals, s_diag/1000, 0, color="orange", alpha=0.15)
ax_s.plot(x_vals, s_diag/1000, color="darkorange", linewidth=3.0)
ax_s.set_ylim(-20, 20) 
ax_s.text(0, (Q_max/1000), f"S={Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="left", va="bottom", fontsize=10, fontweight='bold')
ax_s.text(L, (-Q_max/1000), f"S={-Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="right", va="top", fontsize=10, fontweight='bold')

# d図: 30固定
ax_d.xaxis.set_major_locator(ticker.MultipleLocator(455))
ax_d.grid(True, linestyle="--", alpha=0.3)
ax_d.plot([0, L], [0, 0], 'k-', linewidth=1.5)
ax_d.plot(0, 0, '^k', markersize=10)
ax_d.plot(L, 0, '^k', markersize=10)
ax_d.set_title("d (mm)", loc='left', fontsize=12, fontweight='bold')
ax_d.set_xlim(-150, L + 150)
y_d_plot = np.array([get_delta(x) for x in x_vals])
ax_d.fill_between(x_vals, y_d_plot, 0, color="skyblue", alpha=0.15)
ax_d.plot(x_vals, y_d_plot, color="blue", linewidth=3.0)
ax_d.set_ylim(30, -5) 
ax_d.text(L/2, (delta_max + 1.0), f"d={delta_max:.1f}", color="blue", ha="center", va="bottom", fontsize=11, fontweight='bold')
ax_d.set_xlabel("Position (mm)", fontsize=11)

# 【最終命令】グラフを確実に表示させる
st.pyplot(fig)
