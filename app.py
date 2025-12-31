import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# ページ設定
st.set_page_config(page_title="木製梁のたわみ計算シミュレーター", layout="wide")

# タイトル
st.title("🏗️ 木製梁のたわみ計算シミュレーター")
st.markdown("計算モードを選択して、パラメータを調整してください。")

# --- 1. サイドバー設定 ---
st.sidebar.header("計算モード")
mode = st.sidebar.radio(
    "荷重タイプを選択",
    ("等分布荷重 (全体)", "集中荷重 (中央)")
)

st.sidebar.markdown("---")
st.sidebar.header("共通パラメータ")

wood_materials = {
    "杉 (E=7000 N/mm²)": 7000,
    "桧 (E=9000 N/mm²)": 9000,
    "米松 (E=11000 N/mm²)": 11000,
    "集成材 (E=12000 N/mm²)": 12000,
    "鋼材 (E=205000 N/mm²)": 205000
}
selected_material = st.sidebar.selectbox("樹種を選択", list(wood_materials.keys()))
E = wood_materials[selected_material]

# スパン L (910から455刻みで6000まで)
span_options = list(range(910, 6001, 455))
L = st.sidebar.select_slider("スパン L (mm)", options=span_options, value=3640)

# 梁幅 b
width_options = [105, 120, 150, 180, 210, 240, 270]
b = st.sidebar.select_slider("梁幅 b (mm)", options=width_options, value=120)

# 梁成 h
height_options = [105, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510]
h = st.sidebar.select_slider("梁成 h (mm)", options=height_options, value=240)

I = (b * h**3) / 12

# --- 2. 計算ロジック ---
if mode == "等分布荷重 (全体)":
    st.sidebar.markdown("---")
    st.sidebar.header("荷重設定 (等分布)")
    w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=5.0, step=1.0)
    delta_max = (5 * w * L**4) / (384 * E * I)
    def get_deflection(x):
        return (w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
    load_desc = f"w={w}N/mm"
else:
    st.sidebar.markdown("---")
    st.sidebar.header("荷重設定 (集中)")
    P = st.sidebar.number_input("集中荷重 P (N)", value=18200.0, step=100.0)
    delta_max = (P * L**3) / (48 * E * I)
    def get_deflection(x):
        if x <= L/2:
            return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I)
        else:
            x_mirror = L - x
            return (P * x_mirror * (3*L**2 - 4*x_mirror**2)) / (48 * E * I)
    load_desc = f"P={P}N"

# --- 3. 結果表示 ---
st.subheader(f"計算結果: {mode}")
ratio = int(L / delta_max) if delta_max > 0 else 0
is_ok = delta_max <= (L / 300)

c1, c2, c3 = st.columns(3)
c1.metric("最大たわみ (δmax)", f"{delta_max:.2f} mm")
c2.metric("たわみ比 (1/n)", f"1/{ratio}" if delta_max > 0 else "-")
if is_ok:
    c3.success("判定: OK (1/300 クリア)")
else:
    c3.error("判定: NG (1/300 オーバー)")

# --- 4. グラフ描画 ---
st.markdown("### Deflection Graph")
fig, ax = plt.subplots(figsize=(10, 3.5))
x_vals = np.linspace(0, L, 100)
y_vals = np.array([get_deflection(x) for x in x_vals])

ax.fill_between(x_vals, y_vals, 0, color="skyblue", alpha=0.3)
ax.plot(x_vals, y_vals, color="blue", linewidth=3, label="Deflection Curve")
ax.plot(L/2, delta_max, "ro", markersize=8)

# 数値表示（文字化け回避のため英語のみ）
if delta_max > 60:
    ax.text(L/2, 55, f"{delta_max:.2f}mm (Scale Out)", color="purple", ha="center", fontweight="bold")
else:
    ax.text(L/2, delta_max + 3, f"{delta_max:.2f}mm", color="red", ha="center", fontweight="bold")

# 【文字化け対策】全て英語のラベルに固定
ax.set_title(f"Span:{L}mm / {load_desc} / E:{E}", fontsize=10)
ax.set_xlabel("Position (mm)")
ax.set_ylabel("Deflection (mm)")

# 【修正】横軸目盛りを455刻みに固定
ax.xaxis.set_major_locator(ticker.MultipleLocator(455))

ax.grid(True, linestyle="--", alpha=0.5)
ax.invert_yaxis()
ax.set_ylim(60, -2) # 縦軸 0-60固定

st.pyplot(fig)
