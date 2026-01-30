import streamlit as st
from streamlit_wheel_picker import wheel_picker

# 設定網頁佈局
st.set_page_config(page_title="Pino Logic Matrix", layout="centered")

# --- 核心邏輯函數 ---
def n_m_o_logic(n, m, o):
    """
    通用函數：處理第 n 欄, 第 m 列, 第 o 層
    對應你筆記中的矩陣映射與物理推演
    """
    # 模擬計算：o 層決定了基礎權重，n, m 決定了座標偏移
    base_val = (o * 10)
    result = f"P-{base_val + n + m}"
    return result

# --- UI 介面設計 ---
st.title("多維矩陣系統：滾輪導航")

# 模擬蘋果風格的中央控制區
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    st.write("### 選擇 $o$ 層 (Layer)")
    # 使用 wheel_picker 模擬蘋果滑動感
    # 將 o 層定義為從 1 到 30 (對應你筆記 1/30 的編號)
    layer_options = [f"Layer {i:02d}" for i in range(1, 31)]
    selected_layer_str = wheel_picker(
        key="layer_picker",
        options=layer_options,
        default_index=0
    )
    # 解析出數字 o
    current_o = int(selected_layer_str.split(" ")[1])

st.divider()

# --- 矩陣顯示區 ---
st.subheader(f"當前座標平面：$O$ 軸第 {current_o} 層")

# 定義矩陣規模 (可擴充 n, m)
rows_m = 3
cols_n = 3

# 建立畫布
for m in range(1, rows_m + 1):
    cols = st.columns(cols_n)
    for n in range(1, cols_n + 1):
        with cols[n-1]:
            # 調用通用函數
            node_data = n_m_o_logic(n, m, current_o)
            
            # 渲染卡片 (包含你筆記中的 A, B, C 概念)
            with st.container(border=True):
                st.markdown(f"**$C_{n}, R_{m}$**")
                st.markdown(f"## {node_data}")
                
                # 根據 o 層變動展示不同屬性 (對應感官渲染)
                if current_o < 10:
                    st.caption("🟢 結構解析 (ABC)")
                elif current_o < 20:
                    st.caption("🔵 感官渲染 (動/靜)")
                else:
                    st.caption("🔴 物理公式 (F/v/r)")

# --- 底部擴充功能 ---
with st.expander("查看 $n+i, m+j, o+l$ 擴充邏輯"):
    st.write("""
    1. **n_m_o() 通用化**: 所有的運算都封裝在函數內，不依賴固定索引。
    2. **動態渲染**: 使用迴圈產生 `st.columns`，只需更改 `rows_m` 或 `cols_n` 即可無限擴充。
    3. **狀態保存**: 滾輪選取的 $o$ 值會保存在 `session_state` 中，方便跨層計算。
    """)
