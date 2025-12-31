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
    delta_max = (5 * w * L**4) / (384 * E * I)
    def get_delta(x): return (w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
else:
    P = st.sidebar.number_input("P (N)", value=18200.0)
    M_max, Q_max = (P * L) / 4, P / 2
    m_diag = np.where(x_vals < L/2, (P * x_vals)/2, (P * (L - x_vals))/2)
    s_diag = np.where(x_vals < L/2, P/2, -P/2)
    delta_max = (P * L**3) / (48 * E * I)
    def get_delta(x): 
        return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I) if x <= L/2 else (P * (L-x) * (3*L**2 - 4*(L-x)**2)) / (48 * E * I)

sigma_b, tau = M_max / Z, (1.5 * Q_max) / A
ratio = int(L / delta_max) if delta_max > 0 else 0

# --- 4. 結果表示 ---
st.subheader("📋 断面算定結果")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("曲げ (M) : σb", f"{sigma_b:.2f} N/mm²")
    if sigma_b <= fb: st.success(f"OK (≦{fb:.1f})")
    else: st.error("NG")
with c2:
    st.metric("せん断 (S) : τ", f"{tau:.2f} N/mm²")
    if tau <= fs: st.success(f"OK (≦{fs:.1f})")
    else: st.error("NG")
with c3:
    st.metric("たわみ (d) : δ", f"{delta_max:.2f} mm")
    if delta_max <= L/300: st.success(f"OK (1/{ratio})")
    else: st.error("NG")

# --- 5. 共通描画関数 ---
def create_beam_plot(y_vals, color, y_label, y_lim_top, y_lim_bottom, text_y, text_content, invert=False):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(455))
    ax.tick_params(axis='both', labelsize=10)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.plot([0, L], [0, 0], 'k-', linewidth=1.5)
    ax.plot(0, 0, '^k', markersize=10)
    ax.plot(L, 0, '^k', markersize=10)
    ax.set_xlim(-150, L + 150)
    
    ax.fill_between(x_vals, y_vals, 0, color=color, alpha=0.15)
    ax.plot(x_vals, y_vals, color=color, linewidth=3.0)
    ax.set_ylabel(y_label, fontsize=10, fontweight='bold')
    
    # 軸の範囲固定
    ax.set_ylim(y_lim_top, y_lim_bottom)
    
    # 数値テキストの配置
    ax.text(L/2 if text_y != 0 else 10, text_y, text_content, 
            color=color, ha="center" if text_y != 0 else "left", va="bottom", fontsize=10, fontweight='bold')
    
    return fig

# --- 6. 個別描画セクション ---
st.markdown("---")

# 1. 曲げモーメント図
st.subheader("📊 曲げモーメント図 (BMD)")
fig_m = create_beam_plot(m_diag/1e6, "forestgreen", "M (kN-m)", 20, -5, M_max/1e6 + 0.5, f"M={M_max/1e6:.2f}\n(σb={sigma_b:.2f})")
st.pyplot(fig_m)

# 2. せん断力図
st.subheader("📊 せん断力図 (SFD)")
fig_s = create_beam_plot(s_diag/1000, "darkorange", "S (kN)", -20, 20, 0, "") 
# S図は特殊なのでテキストを個別追加
ax_s = fig_s.get_axes()[0]
ax_s.text(0, Q_max/1000, f"S={Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="left", va="bottom", fontsize=10, fontweight='bold')
ax_s.text(L, -Q_max/1000, f"S={-Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="right", va="top", fontsize=10, fontweight='bold')
st.pyplot(fig_s)

# 3. たわみ図
st.subheader("📊 たわみ図 (Deflection)")
fig_d = create_beam_plot(np.array([get_delta(x) for x in x_vals]), "blue", "d (mm)", 30, -5, delta_max + 1.0, f"d={delta_max:.1f}")
ax_d = fig_d.get_axes()[0]
ax_d.set_xlabel("Position (mm)", fontsize=11)
st.pyplot(fig_d)
