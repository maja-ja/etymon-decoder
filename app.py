import streamlit as st

st.set_page_config(page_title="Etymon Matrix Editor", layout="centered")

st.title("🧩 詞源九宮格編輯矩陣")
st.write("點選下方按鈕，將左側輸入的內容填入對應的座標。")

# --- 側邊欄：內容輸入區 ---
st.sidebar.header("內容設置")
input_text = st.sidebar.text_input("要填入的內容 (如：字根、感官描述)", value="Core")

# 初始化 Session State (確保重新整理時資料不消失)
if 'matrix_data' not in st.session_state:
    # 建立 3x3 的空矩陣
    st.session_state.matrix_data = [["" for _ in range(3)] for _ in range(3)]

# 定義坐標標籤 (呼應筆記中的 X, Y, Z)
cols_label = ["X", "Y", "Z"]
rows_label = ["1 (靜)", "2 (動)", "3 (感)"]

# --- 主畫面：九宮格佈局 ---
# 建立表頭
header_cols = st.columns([1, 2, 2, 2])
header_cols[1].markdown("**X (核心/字首)**")
header_cols[2].markdown("**Y (連結/字根)**")
header_cols[3].markdown("**Z (邊界/詞尾)**")

# 建立 3x3 矩陣
for i in range(3):
    cols = st.columns([1, 2, 2, 2])
    cols[0].write(f"**{rows_label[i]}**") # 縱軸標籤
    
    for j in range(3):
        with cols[j+1]:
            # 顯示當前格子的內容
            current_val = st.session_state.matrix_data[i][j]
            box_label = f"{current_val}" if current_val else "➕ 點擊填入"
            
            # 使用按鈕作為觸發器
            if st.button(box_label, key=f"btn_{i}_{j}", use_container_width=True):
                st.session_state.matrix_data[i][j] = input_text
                st.rerun() # 立即重新渲染顯示更新

# --- 功能操作 ---
st.divider()
if st.button("清除所有格子"):
    st.session_state.matrix_data = [["" for _ in range(3)] for _ in range(3)]
    st.rerun()

# --- 數據導出 (模擬筆記結構) ---
with st.expander("查看矩陣 JSON 數據"):
    st.json(st.session_state.matrix_data)
