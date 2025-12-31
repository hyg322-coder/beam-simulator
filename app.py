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
w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=15.0, step=1.0, help="長期荷重+積載荷重などを想定")

# --- 計算処理 ---
# 断面二次モーメント I = bh^3 / 12
I = (b * h**3) / 12
# 最大たわみ delta = (5 * w * L^4) / (384 * E * I)
delta_max = (5 * w * L**4) / (384 * E * I)
# たわみ比 1/n
deflection_ratio = L / delta_max if delta_max != 0 else 0

# --- メインエリア：結果表示 ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="最大たわみ (δmax)", value=f"{delta_max:.2f} mm")
with col2:
    st.metric(label="たわみ比 (1/n)", value=f"1/{deflection_ratio:.0f}")
with col3:
    # 判定ロジック（例: 1/300以下ならOK）
    limit = 300
    if deflection_ratio >= limit:
        st.success(f"判定: OK (1/{limit} クリア)")
    else:
        st.error(f"判定: NG (1/{limit} オーバー)")

# 4. グラフ描画
st.subheader("Deflection Graph")

fig, ax = plt.subplots(figsize=(10, 5))

# グラフのプロット（英語ラベル）
ax.plot(x, y, label="Deflection Curve", color="blue", linewidth=3)
ax.fill_between(x, y, 0, color="skyblue", alpha=0.3)

# タイトルと軸ラベル（文字化け回避のため英語表記）
ax.set_title(f"Span: {L}mm / Section: {b}x{h}mm / E: {E} N/mm2", fontsize=14)
ax.set_xlabel("Position (mm)", fontsize=12)
ax.set_ylabel("Deflection (mm)", fontsize=12)

# ★Y軸の表示範囲を調整（たわみが小さくてもペチャンコに見えないようにする）
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
