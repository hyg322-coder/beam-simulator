import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

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

# 樹種の選択
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

# 梁幅 b (指定のサイズリスト)
width_options = [105, 120, 150, 180, 210, 240, 270]
b = st.sidebar.select_slider("梁幅 b (mm)", options=width_options, value=120)

# 梁成 h (480, 510を含む指定リスト)
height_options = [105, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510]
h = st.sidebar.select_slider("梁成 h (mm)", options=height_options, value=240)

# 断面二次モーメント I
I = (b * h**3) / 12

# --- 2. 計算ロジック ---

if mode == "等分布荷重 (全体)":
    st.sidebar.markdown("---")
    st.sidebar.header("荷重設定 (等分布)")
    w = st.sidebar.number_input("等分布荷重 w (N/mm)", value=5.0, step=1.0)
    
    # 公式: 5wL^4 / 384EI
    delta_max = (5 * w * L**4) / (384 * E * I)
    
    def get_deflection(x):
        return (w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
        
    load_desc = f"w={w} N/mm"

else: # 集中荷重 (中央)
    st.sidebar.markdown("---")
    st.sidebar.header("荷重設定 (集中)")
    # デフォルト値を等分布荷重5N相当（18200）に設定
    P = st.sidebar.number_input("集中荷重 P (N)", value=18200.0, step=100.0)
    
    # 公式: PL^3 / 48EI
    delta_max = (P * L**3) / (48 * E * I)
    
    def get_deflection(x):
        if x <= L/2:
            return (P * x * (3*L**2 - 4*x**2)) / (48 * E * I)
        else:
            x_mirror = L - x
            return (P * x_mirror * (3*L**2 - 4*x_mirror**2)) / (48 * E * I)
            
    load_desc = f"P={P} N"

# --- 3. 結果表示 ---
st.subheader(f"計算結果: {mode}")

if delta_max > 0:
    ratio = int(L / delta_max)
else:
    ratio = 0
limit = L / 300
is_ok = delta_max <= limit

c1, c2, c3 = st.columns(3)
c1.metric("最大たわみ (δmax)", f"{delta_max:.2f} mm")
c2.metric("たわみ比 (1/n)", f"1/{ratio}" if delta_max > 0 else "-")

if is_ok:
    c3.success("判定: OK (1/300 クリア)")
else:
    c3.error("判定: NG (1/300 オーバー)")

# --- 4. グラフ描画 ---
st.markdown("### Deflection Graph")

# グラフの高さを少し縮めて画面に収まりやすく調整
fig, ax = plt.subplots(figsize=(10, 3.2))
x_vals = np.linspace(0, L, 100)

y_vals = np.array([get_deflection(x) for x in x_vals])

# 塗りつぶし & 線
ax.fill_between(x_vals, y_vals, 0, color="skyblue", alpha=0.3)
ax.plot(x_vals, y_vals, color="blue", linewidth=3, label="Deflection")

# 最大点のプロット
ax.plot(L/2, delta_max, "ro", markersize=8)

# テキスト表示制御
if delta_max > 60:
    display_y = 55
    text_content = f"{delta_max:.2f}mm (Scale Out)"
    text_color = "purple"
else:
    display_y = delta_max + 2
    text_content = f"{delta_max:.2f}mm"
    text_color = "red"

# 【修正点】文字化けを防ぐため、標準的なサンセリフ体フォントを明示的に指定
font_style = {'family': 'sans-serif', 'weight': 'bold', 'size': 12}
ax.text(L/2, display_y, text_content, 
        color=text_color, ha="center", fontdict=font_style)

# 装飾（グラフ内の文字は英語表記で統一し、文字化けを回避）
ax.set_title(f"Span: {L}mm / {load_desc} / E: {E}", fontsize=12)
ax.set_xlabel("Position (mm)")
ax.set_ylabel("Deflection (mm)")
ax.grid(True, linestyle="--", alpha=0.7)
ax.legend(loc="upper right")

# Y軸反転
ax.invert_yaxis()

# グラフ範囲固定（0〜60mm）
ax.set_ylim(60, -2) 

st.pyplot(fig)
