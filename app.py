import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ページ設定
st.set_page_config(page_title="梁たわみシミュレーター", layout="wide")

# --- タイトルと説明 ---
st.title("🏗️ 木製梁のたわみ計算シミュレーター")
st.markdown("""
単純梁に等分布荷重がかかった場合のたわみをリアルタイムで計算・可視化します。
スライダーを動かして、断面寸法やスパンによる挙動の変化を確認してください。
""")

# --- サイドバー：パラメータ入力 ---
st.sidebar.header("パラメータ設定")

# 1. 樹種とヤング係数
wood_materials = {
    "杉 (E=7000 N/mm²)": 7000,
    "桧 (E=9000 N/mm²)": 9000,
    "松 (E=10000 N/mm²)": 10000,
    "ベイマツ (E=12000 N/mm²)": 12000,
    "カスタム設定": 0
}
selected_material = st.sidebar.selectbox("樹種を選択", list(wood_materials.keys()))

if selected_material == "カスタム設定":
    E = st.sidebar.number_input("ヤング係数 E (N/mm²)", value=8000, step=500)
else:
    E = wood_materials[selected_material]
    st.sidebar.text(f"E = {E} N/mm²")

# 2. 寸法と荷重
L = st.sidebar.slider("スパン L (mm)", min_value=1820, max_value=7280, value=3640, step=910)
b = st.sidebar.slider("梁幅 b (mm)", min_value=105, max_value=240, value=120, step=15)
h = st.sidebar.slider("梁成 h (mm)", min_value=105, max_value=450, value=240, step=15)
w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=15.0, step=1.0)

# --- 3. 計算実行 (ここが消えていました！) ---
# 断面二次モーメント I
I = b * h**3 / 12

# 最大たわみ δmax (mm)
delta_max = (5 * w * L**4) / (384 * E * I)

# たわみ曲線 y(x) の計算
x = np.linspace(0, L, 100)
y = - (w * x / (24 * E * I)) * (L**3 - 2*L * x**2 + x**3)

# 判定 (1/300)
allowable_deflection = L / 300
if delta_max <= allowable_deflection:
    result_text = "OK (1/300 クリア)"
    result_color = "success"
else:
    result_text = "NG (1/300 オーバー)"
    result_color = "error"

# --- 結果表示 ---
c1, c2, c3 = st.columns(3)
c1.metric("最大たわみ (δmax)", f"{delta_max:.2f} mm")
c2.metric("たわみ比 (1/n)", f"1/{int(L/delta_max)}")

if result_color == "success":
    c3.success(f"判定: {result_text}")
else:
    c3.error(f"判定: {result_text}")

# --- 4. グラフ描画 (英語表記＆Y軸調整版) ---
st.subheader("Deflection Graph")

fig, ax = plt.subplots(figsize=(10, 3.5)

# グラフのプロット
ax.plot(x, y, label="Deflection Curve", color="blue", linewidth=3)
ax.fill_between(x, y, 0, color="skyblue", alpha=0.3)

# タイトルと軸ラベル (文字化け対策で英語)
ax.set_title(f"Span: {L}mm / Section: {b}x{h}mm / E: {E} N/mm2", fontsize=14)
ax.set_xlabel("Position (mm)", fontsize=12)
ax.set_ylabel("Deflection (mm)", fontsize=12)

# Y軸の範囲設定 (たわみが小さくても見やすく調整)
current_limit = -delta_max * 1.5
view_limit = min(-25, current_limit) # 最低でも-25mmまでは表示
ax.set_ylim(view_limit, 5)

# グリッドと凡例
ax.grid(True, linestyle="--", alpha=0.6)
ax.legend()

# 最大たわみ位置のプロット
ax.plot(L/2, -delta_max, "ro")
ax.text(L/2, -delta_max - (abs(view_limit)*0.05), f"{delta_max:.2f}mm", color="red", ha="center", fontsize=12, fontweight="bold")

st.pyplot(fig)
