import streamlit as st
import pandas as pd

# 設置頁面標題，呼應你的影片標題
st.set_page_config(page_title="Etymon Decoder Matrix", layout="wide")

st.title("🧩 Etymon Decoder: 九宮格解析矩陣")
st.write("根據設計者 PINO 的結構解析與感官渲染模型")

# --- 側邊欄：輸入區 ---
st.sidebar.header("輸入單字結構")
prefix = st.sidebar.text_input("A: 核心/字首 (X)", value="re-")
root = st.sidebar.text_input("B: 連結/字根 (Y)", value="voke")
suffix = st.sidebar.text_input("C: 邊界/詞尾 (Z)", value="-ation")

# --- 邏輯運算：模擬物理公式運算 ---
# 筆記提到 F = m * v... 這裡我們模擬一個「語義衝力 (Semantic Force)」
semantic_mass = len(root)
semantic_velocity = len(prefix)
force = semantic_mass * semantic_velocity

# --- 顯示區：九宮格矩陣 ---
st.subheader(f"單字解析：{prefix}{root}{suffix}")
st.metric(label="語義衝力 (Force = m * v)", value=f"{force} N", help="模擬筆記中的 F=ma 邏輯")

# 定義縱軸與橫軸
rows = ["靜態 (顏色/形狀/位置)", "動態 (速度/阻力/方向)", "感覺 (心理/有序無序)"]
cols = [f"A: {prefix}", f"B: {root}", f"C: {suffix}"]

# 建立九宮格佈局
for i in range(3):
    columns = st.columns(3)
    for j in range(3):
        with columns[j]:
            # 根據筆記 [5] 的感官描述填入邏輯
            content = ""
            if i == 0: # 靜態
                content = f"📍 定位 {cols[j]} 的視覺屬性"
            elif i == 1: # 動態
                content = f"⚡ 分析 {cols[j]} 的運動方向"
            else: # 感覺
                content = f"🧠 {cols[j]} 產生的心理共鳴"
            
            st.info(f"**{rows[i]}**\n\n{content}")

# --- 底部：數據洞察模擬 ---
st.divider()
st.subheader("📊 流量洞察回饋 (模擬)")
st.write("根據你關閉帳號前的數據，這類結構解析最受 25-44 歲用戶歡迎。")
