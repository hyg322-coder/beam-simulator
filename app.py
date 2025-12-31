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
    E, fb, fs = st.sidebar.number_input("E", value=7000), st.sidebar.number_input("fb", value=10.0), st.sidebar.number_input("fs", value=0.8)
else:
    E, fb, fs = material_db[selected_label].values()

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
    def get_delta(x): return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I) if x <= L/2 else (P * (L-x) * (3*L**2 - 4*(L-x)**2)) / (48 * E * I)

sigma_b, tau = M_max / Z, (1.5 * Q_max) / A
ratio = int(L / delta_max) if delta_max > 0 else 0

# --- 4. 結果表示（記号 M, S, d を追加） ---
st.subheader("📋 断面算定結果")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("曲げ (M) : σb", f"{sigma_b:.2f} N/mm²")
    _ = st.success(f"OK (≦{fb:.1f})") if sigma_b <= fb else st.error("NG")
with c2:
    st.metric("せん断 (S) : τ", f"{tau:.2f} N/mm²")
    _ = st.success(f"OK (≦{fs:.1f})") if tau <= fs else st.error("NG")
with c3:
    st.metric("たわみ (d) : δ", f"{delta_max:.2f} mm")
    _ = st.success(f"OK (1/{ratio})") if delta_max <= L/300 else st.error("NG")

# --- 5. グラフ描画 ---
st.markdown("### 📊 応力・変形図")
fig, (ax_m, ax_s, ax_d) = plt.subplots(3, 1, figsize=(10, 3.8), sharex=True)
plt.subplots_adjust(hspace=1.5)

def decorate(ax, label_text, unit):
    ax.xaxis.set_major_locator(ticker.MultipleLocator(455))
    ax.tick_params(axis='both', labelsize=7)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.plot([0, L], [0, 0], 'k-', linewidth=0.8)
    ax.plot(0, 0, '^k', markersize=5)
    ax.plot(L, 0, '^k', markersize=5)
    ax.set_title(f"{label_text} ({unit})", loc='left', fontsize=8, fontweight='bold', pad=2)

# M図
ax_m.fill_between(x_vals, m_diag/1e6, 0, color="green", alpha=0.15)
ax_m.plot(x_vals, m_diag/1e6, color="forestgreen", linewidth=1.5)
decorate(ax_m, "M", "kN-m")
ax_m.invert_yaxis()
ax_m.text(L/2, M_max/1e6, f"M={M_max/1e6:.2f}\n(σb={sigma_b:.2f})", color="forestgreen", ha="center", va="top", fontsize=7, fontweight='bold')

# S図
ax_s.fill_between(x_vals, s_diag/1000, 0, color="orange", alpha=0.15)
ax_s.plot(x_vals, s_diag/1000, color="darkorange", linewidth=1.5)
lim_s = max(abs(Q_max/1000) * 1.6, 5)
ax_s.set_ylim(lim_s, -lim_s) # 上がプラス
decorate(ax_s, "S", "kN")
ax_s.text(0, Q_max/1000, f"S={Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="left", va="bottom", fontsize=7, fontweight='bold')
ax_s.text(L, -Q_max/1000, f"S={-Q_max/1000:.1f}\n(τ={tau:.2f})", color="darkorange", ha="right", va="top", fontsize=7, fontweight='bold')

# d図
y_d = np.array([get_delta(x) for x in x_vals])
ax_d.fill_between(x_vals, y_d, 0, color="skyblue", alpha=0.15)
ax_d.plot(x_vals, y_d, color="blue", linewidth=1.5)
decorate(ax_d, "d", "mm")
ax_d.invert_yaxis()
ax_d.set_ylim(60, -25)
ax_d.annotate('', xy=(0, -12), xytext=(L, -12), arrowprops=dict(arrowstyle='<->', color='gray', lw=0.6))
ax_d.text(L/2, -15, f"L={L}mm", ha='center', color='gray', fontsize=8, fontweight='bold')
ax_d.text(L/2, delta_max, f"d={delta_max:.1f}", color="blue", ha="center", va="top", fontsize=8, fontweight='bold')

st.pyplot(fig)
