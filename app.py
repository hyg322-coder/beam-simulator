import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# ページ設定
st.set_page_config(page_title="大梁断面算定シミュレーター", layout="wide")

st.title("🏗️ 大梁断面算定シミュレーター")
st.markdown("曲げ・せん断・たわみの3要素をピン接合（単純梁）として算定・可視化します。")

# --- 1. データベース (長期許容応力度: N/mm2) ---
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
    E = st.sidebar.number_input("ヤング係数 E (N/mm²)", value=7000)
    fb = st.sidebar.number_input("許容曲げ応力度 fb (N/mm²)", value=10.0)
    fs = st.sidebar.number_input("許容せん断応力度 fs (N/mm²)", value=0.8)
else:
    E = material_db[selected_label]["E"]
    fb = material_db[selected_label]["fb"]
    fs = material_db[selected_label]["fs"]

span_options = list(range(910, 6001, 455))
L = st.sidebar.select_slider("スパン L (mm)", options=span_options, value=3640)
b = st.sidebar.select_slider("梁幅 b (mm)", options=[105, 120, 150, 180, 210, 240, 270], value=120)
h = st.sidebar.select_slider("梁成 h (mm)", options=[105, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510], value=240)

# --- 3. 計算ロジック ---
Z = (b * h**2) / 6
A = b * h
I = (b * h**3) / 12
x_vals = np.linspace(0, L, 100)

if mode == "等分布荷重 (全体)":
    w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=5.0)
    M_max = (w * L**2) / 8
    Q_max = (w * L) / 2
    delta_max = (5 * w * L**4) / (384 * E * I)
    s_diagram = (w * L / 2) - (w * x_vals)
    m_diagram = (w * x_vals / 2) * (L - x_vals)
    def get_delta(x): return (w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
    load_desc = f"w={w}N/mm"
else:
    P = st.sidebar.number_input("集中荷重 P (N)", value=18200.0)
    M_max = (P * L) / 4
    Q_max = P / 2
    delta_max = (P * L**3) / (48 * E * I)
    s_diagram = np.where(x_vals < L/2, P/2, -P/2)
    m_diagram = np.where(x_vals < L/2, (P * x_vals)/2, (P * (L - x_vals))/2)
    def get_delta(x): 
        return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I) if x <= L/2 else (P * (L-x) * (3*L**2 - 4*(L-x)**2)) / (48 * E * I)
    load_desc = f"P={P}N"

sigma_b = M_max / Z
tau = (1.5 * Q_max) / A
ratio = int(L / delta_max) if delta_max > 0 else 0

# --- 4. 結果表示（修正：エラー回避版） ---
st.subheader("📋 断面算定結果")
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("曲げ σb", f"{sigma_b:.2f} N/mm²")
    if sigma_b <= fb:
        st.success(f"OK (≦{fb:.1f})")
    else:
        st.error(f"NG (>{fb:.1f})")

with c2:
    st.metric("せん断 τ", f"{tau:.2f} N/mm²")
    if tau <= fs:
        st.success(f"OK (≦{fs:.1f})")
    else:
        st.error(f"NG (>{fs:.1f})")

with c3:
    st.metric("最大たわみ δ", f"{delta_max:.2f} mm")
    if delta_max <= L/300:
        st.success(f"OK (1/{ratio})")
    else:
        st.error(f"NG (1/{ratio})")

# --- 5. グラフ描画 (S図・M図・たわみ図) ---
st.markdown("---")
st.markdown("### 📊 応力・変形図")
fig, (ax_s, ax_m, ax_d) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
plt.subplots_adjust(hspace=0.4)

# S図
ax_s.fill_between(x_vals, s_diagram, 0, color="orange", alpha=0.3)
ax_s.plot(x_vals, s_diagram, color="darkorange")
ax_s.set_ylabel("Shear (N)")
ax_s.grid(True, linestyle="--", alpha=0.5)
ax_s.set_title("Shear Force Diagram (S)", loc='left', fontsize=9)

# M図
ax_m.fill_between(x_vals, m_diagram, 0, color="green", alpha=0.3)
ax_m.plot(x_vals, m_diagram, color="forestgreen")
ax_m.set_ylabel("Bending (N-mm)")
ax_m.grid(True, linestyle="--", alpha=0.5)
ax_m.set_title("Bending Moment Diagram (M)", loc='left', fontsize=9)

# たわみ図
y_delta = np.array([get_delta(x) for x in x_vals])
ax_d.fill_between(x_vals, y_delta, 0, color="skyblue", alpha=0.3)
ax_d.plot(x_vals, y_delta, color="blue", linewidth=2)
ax_d.set_ylabel("Deflection (mm)")
ax_d.invert_yaxis()
ax_d.set_ylim(60, -2)
ax_d.grid(True, linestyle="--", alpha=0.5)
ax_d.set_title("Deflection Curve", loc='left', fontsize=9)

ax_d.set_xlabel("Position (mm)")
ax_d.xaxis.set_major_locator(ticker.MultipleLocator(455))
st.pyplot(fig)
