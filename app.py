import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# ページ設定
st.set_page_config(page_title="大梁断面算定シミュレーター", layout="wide")

st.title("🏗️ 大梁断面算定シミュレーター")
st.markdown("曲げ・せん断・たわみの3要素をピン接合（単純梁）として算定します。")

# --- 1. データベース（長期許容応力度: N/mm2） ---
# 一般的な数値をプリセット。任意入力時はこれらを基準に調整可能。
material_db = {
    "杉 (E70)": {"E": 7000, "fb": 15.0/1.5, "fs": 1.2/1.5}, # 長期として安全側設定
    "桧 (E90)": {"E": 9000, "fb": 17.0/1.5, "fs": 1.5/1.5},
    "米松 (E110)": {"E": 11000, "fb": 20.0/1.5, "fs": 1.8/1.5},
    "集成材 (E120)": {"E": 12000, "fb": 22.0/1.5, "fs": 2.0/1.5},
    "任意入力": {"E": 7000, "fb": 15.0, "fs": 1.2}
}

# --- 2. サイドバー設定 ---
st.sidebar.header("1. 荷重条件")
mode = st.sidebar.radio("荷重タイプ", ("等分布荷重 (全体)", "集中荷重 (中央)"))

st.sidebar.markdown("---")
st.sidebar.header("2. 材料・断面")
selected_label = st.sidebar.selectbox("樹種選択", list(material_db.keys()))

if selected_label == "任意入力":
    E = st.sidebar.number_input("ヤング係数 E", value=7000)
    fb = st.sidebar.number_input("許容曲げ応力度 fb", value=10.0)
    fs = st.sidebar.number_input("許容せん断応力度 fs", value=0.8)
else:
    E = material_db[selected_label]["E"]
    fb = material_db[selected_label]["fb"]
    fs = material_db[selected_label]["fs"]

span_options = list(range(910, 6001, 455))
L = st.sidebar.select_slider("スパン L (mm)", options=span_options, value=3640)
b = st.sidebar.select_slider("梁幅 b (mm)", options=[105, 120, 150, 180, 210, 240, 270], value=120)
h = st.sidebar.select_slider("梁成 h (mm)", options=[105, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510], value=240)

# --- 3. 計算セクション ---
Z = (b * h**2) / 6    # 断面係数
A = b * h             # 断面積
I = (b * h**3) / 12   # 断面二次モーメント

if mode == "等分布荷重 (全体)":
    w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=5.0)
    M_max = (w * L**2) / 8
    Q_max = (w * L) / 2
    delta_max = (5 * w * L**4) / (384 * E * I)
    def get_delta(x): return (w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
    load_desc = f"w={w}N/mm"
else:
    P = st.sidebar.number_input("集中荷重 P (N)", value=18200.0)
    M_max = (P * L) / 4
    Q_max = P / 2
    delta_max = (P * L**3) / (48 * E * I)
    def get_delta(x): 
        return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I) if x <= L/2 else (P * (L-x) * (3*L**2 - 4*(L-x)**2)) / (48 * E * I)
    load_desc = f"P={P}N"

# 応力度計算
sigma_b = M_max / Z
tau = (1.5 * Q_max) / A
ratio = int(L / delta_max) if delta_max > 0 else 0

# --- 4. 結果表示 ---
st.subheader("📋 断面算定結果")
col1, col2, col3 = st.columns(3)

# 曲げ判定
with col1:
    st.write("**【曲げ】**")
    st.metric("曲げ応力度 σb", f"{sigma_b:.2f}")
    if sigma_b <= fb: st.success(f"OK (≦{fb:.1f})")
    else: st.error(f"NG (>{fb:.1f})")

# せん断判定
with col2:
    st.write("**【せん断】**")
    st.metric("せん断応力度 τ", f"{tau:.2f}")
    if tau <= fs: st.success(f"OK (≦{fs:.1f})")
    else: st.error(f"NG (>{fs:.1f})")

# たわみ判定
with col3:
    st.write("**【たわみ】**")
    st.metric("最大たわみ δ", f"{delta_max:.2f}")
    if delta_max <= L/300: st.success(f"OK (1/{ratio})")
    else: st.error(f"NG (1/{ratio})")

# --- 5. グラフ描画 ---
st.markdown("---")
fig, ax = plt.subplots(figsize=(10, 3.2))
x_vals = np.linspace(0, L, 100)
y_vals = np.array([get_delta(x) for x in x_vals])
ax.fill_between(x_vals, y_vals, 0, color="skyblue", alpha=0.3)
ax.plot(x_vals, y_vals, color="blue", linewidth=3)
ax.plot(L/2, delta_max, "ro")

# 文字化け対策
if delta_max > 60:
    ax.text(L/2, 55, f"{delta_max:.2f}mm (Scale Out)", color="purple", ha="center", fontweight="bold")
else:
    ax.text(L/2, delta_max + 3, f"{delta_max:.2f}mm", color="red", ha="center", fontweight="bold")

ax.set_title(f"Span:{L}mm / {load_desc} / E:{E}", fontsize=10)
ax.xaxis.set_major_locator(ticker.MultipleLocator(455))
ax.grid(True, linestyle="--", alpha=0.5)
ax.invert_yaxis()
ax.set_ylim(60, -2)
st.pyplot(fig)
