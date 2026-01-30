import streamlit as st

# --- 核心通用函數 ---
def n_m_o_logic(n, m, o):
    """
    通用邏輯：處理第 n 欄, 第 m 列, 第 o 層
    將來擴充 n+i, m+j, o+l 只需要修改調用範圍
    """
    # 這裡實作你筆記中的物理與感官邏輯映射
    if o == 1: # 假設第 1 層是結構層
        return f"結構(A/B/C): {n}-{m}"
    elif o == 2: # 假設第 2 層是感官渲染
        return f"感官(動/靜): {n*o}"
    else: # 假設第 3 層以上是物理公式
        return f"F = {n} * {m} * {o} (N)"

# --- UI 佈局 ---
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .stSlider [data-baseweb="slider"] {
        width: 80%;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Pino 邏輯建模：n x m x o 多維系統")

# --- 層指示器 (O 層控制) ---
# 用蘋果風格的 slider 模擬 o 軸
st.subheader("層指示器 (o-axis)")
o_selector = st.select_slider(
    "滑動以切換不同深度的邏輯層 (o)",
    options=[i for i in range(1, 31)],
    value=1
)

st.divider()

# --- 矩陣顯示區 (N 欄 x M 列) ---
st.header(f"當前觀測面：第 {o_selector} 層")

# 定義維度 (方便未來 n+i, m+j 擴充)
rows_m = 3
cols_n = 3

for m in range(1, rows_m + 1):
    cols = st.columns(cols_n)
    for n in range(1, cols_n + 1):
        with cols[n-1]:
            # 這裡就是你要求的：每一格都調用同一個函數
            result = n_m_o_logic(n, m, o_selector)
            
            with st.container(border=True):
                st.write(f"**座標 ({n}, {m}, {o_selector})**")
                st.info(result)

# --- 邏輯示範圖解 ---
st.divider()
st.subheader("系統架構說明")
st.write("這是一個三維張量結構的切片展示：")
# 插入圖解以幫助解釋 n x m x o 的幾何關係
#
