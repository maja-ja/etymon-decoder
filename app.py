import streamlit as st

# 設定網頁標題
st.title("多維邏輯系統：層級導航器")

# --- 1. 定義通用邏輯函數 ---
def n_m_o_logic(n, m, o):
    """
    這是你要求的通用函數，處理第 n 欄, 第 m 列, 第 o 層。
    將來擴充 n+i, m+j, o+l 時，邏輯依然通用。
    """
    # 模擬你筆記中的矩陣運算，例如：座標權重計算
    calc_result = (n * 100) + (m * 10) + o 
    return f"核: {calc_result}"

# --- 2. 側邊欄控制擴充需求 ---
with st.sidebar:
    st.header("維度擴充設定")
    max_o = st.number_input("總層數 (o)", min_value=1, value=5)
    max_m = st.number_input("總列數 (m)", min_value=1, value=3)
    max_n = st.number_input("總欄數 (n)", min_value=1, value=3)
    
    st.divider()
    # --- 層指示器 (Layer Indicator) ---
    # 使用 slider 作為指示器，直接控制變數 o
    current_o = st.slider("層指示器 (o-axis)", 1, max_o, 1)

# --- 3. 根據指示器顯示當前層級內容 ---
st.header(f"當前檢視：第 {current_o} 層 (Layer O={current_o})")

# 建立表格佈局
for m_idx in range(1, max_m + 1):
    cols = st.columns(max_n)
    for n_idx in range(1, max_n + 1):
        with cols[n_idx-1]:
            # 調用通用函數
            result = n_m_o_logic(n_idx, m_idx, current_o)
            
            # UI 呈現
            with st.container(border=True):
                st.markdown(f"**座標 ({n_idx},{m_idx})**")
                st.code(result)
                
                # 示範層級間的變化：如果 o 層數不同，顏色也不同
                if current_o % 2 == 0:
                    st.caption("⚡ 偶數層模式")
                else:
                    st.caption("🌀 奇數層模式")

# --- 4. 數據穿透示範 (Cross-layer Logic) ---
st.divider()
st.subheader("層級穿透分析")
target_n = st.selectbox("選擇欄 (n)", range(1, max_n + 1))
target_m = st.selectbox("選擇列 (m)", range(1, max_m + 1))

if st.button("分析該點在所有層的演化"):
    history = [n_m_o_logic(target_n, target_m, i) for i in range(1, max_o + 1)]
    st.write(f"點 ({target_n},{target_m}) 在 1~{max_o} 層的邏輯路徑：")
    st.line_chart([int(h.split(": ")[1]) for h in history])
