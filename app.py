import streamlit as st
import json
import random
import os

# --- 基礎設定 ---
DB_FILE = 'etymon_database.json'

# --- 1. 密碼檢查功能 ---
def check_password():
    """要求輸入密碼，正確才顯示內容"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # 登入介面
    st.title("🔐 歡迎來到詞根宇宙")
    st.markdown("這是私人的單字學習空間，請輸入密碼以繼續。")
    password = st.text_input("訪問密碼：", type="password")
    if st.button("登入"):
        if password == "8888":  # <--- 在這裡修改你的密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤")
    return False

# 如果密碼沒過，停止執行後續程式
if not check_password():
    st.stop()

# --- 2. 數據處理函式 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(new_data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

data = load_data()

# --- 3. 側邊欄與模式導航 ---
st.sidebar.title("🚀 詞根宇宙導航")
st.sidebar.markdown("---")
mode = st.sidebar.radio("請選擇功能模式：", ["🔍 搜尋解碼", "✍️ 學習測驗", "⚙️ 數據管理"])

# --- 模式 A：搜尋解碼 (原本的功能) ---
if mode == "🔍 搜尋解碼":
    st.title("🧩 Etymon Decoder 語源解碼器")
    
    # 側邊欄分類選擇
    all_categories = [item['category'] for item in data]
    selected_cat = st.sidebar.selectbox("選擇知識領域", all_categories)
    
    search_query = st.text_input("🔍 輸入單字或詞根來解碼...", placeholder="例如: Predict, Bio, Port...")

    if search_query:
        query = search_query.lower()
        found = False
        for cat in data:
            for group in cat['root_groups']:
                root_match = any(query in r.lower() for r in group['roots'])
                words_match = [v for v in group['vocabulary'] if query in v['word'].lower()]
                
                if root_match or words_match:
                    found = True
                    st.divider()
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"### 詞根: `{' / '.join(group['roots'])}`")
                        st.write(f"**核心含義:** {group['meaning']}")
                    with col2:
                        for v in group['vocabulary']:
                            display_text = f"**{v['word']}** \n解構: `{v['breakdown']}` | 含義: {v['definition']}"
                            if query in v['word'].lower():
                                st.success(display_text)
                            else:
                                st.write(display_text)
        if not found:
            st.warning("找不到相關結果。")
    else:
        st.info("💡 請在上方輸入單字，或從左側側邊欄瀏覽分類。")

# --- 模式 B：學習測驗 (新增的功能) ---
elif mode == "✍️ 學習測驗":
    st.title("✍️ 詞根解碼挑戰")
    
    # 展平數據庫單字
    all_words = []
    for cat in data:
        for group in cat['root_groups']:
            for v in group['vocabulary']:
                all_words.append({**v, "root_meaning": group['meaning']})

    if not all_words:
        st.warning("資料庫中沒有單字。")
    else:
        if 'q' not in st.session_state:
            st.session_state.q = random.choice(all_words)
            st.session_state.revealed = False

        q = st.session_state.q
        st.subheader(f"單字：:blue[{q['word']}]")
        st.write(f"提示（詞根含義）：{q['root_meaning']}")

        ans_type = st.radio("你想測試什麼？", ["猜中文含義", "猜拆解邏輯"])
        user_input = st.text_input("請輸入答案：")

        if st.button("查看解答"):
            st.session_state.revealed = True
            if st.session_state.revealed:
                target_ans = q['definition'] if ans_type == "中文含義" else q['breakdown']
                st.info(f"正確答案：{target_ans}")
                st.balloons() # 答對了或是看解答的小效果

        if st.button("下一題"):
            st.session_state.q = random.choice(all_words)
            st.session_state.revealed = False
            st.rerun()

# --- 模式 C：數據管理 (手動貼 JSON) ---
elif mode == "⚙️ 數據管理":
    st.title("🛠 數據庫手動更新")
    st.markdown("當 Gemini 產出新的詞根數據時，請將整段 JSON 代碼貼在下方：")
    
    current_json_str = json.dumps(data, indent=4, ensure_ascii=False)
    new_json_str = st.text_area("JSON 數據區 (可直接編輯)", value=current_json_str, height=500)
    
    if st.button("💾 儲存並更新資料庫"):
        try:
            new_data = json.loads(new_json_str)
            save_data(new_data)
            st.success("資料庫已成功更新！")
            st.cache_data.clear() # 清除快取以確保讀取最新資料
        except Exception as e:
            st.error(f"JSON 格式有誤：{e}")

# --- 頁尾 ---
st.sidebar.markdown("---")
st.sidebar.info("詞根宇宙 v1.0 - AI 共同開發")