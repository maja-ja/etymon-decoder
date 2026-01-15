import streamlit as st
import json
import random
import os
import re

# --- 基礎設定 ---
DB_FILE = 'etymon_database.json'

# --- 1. 密碼檢查功能 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.title("🔐 歡迎來到詞根宇宙")
    password = st.text_input("訪問密碼：", type="password")
    if st.button("登入"):
        if password == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤")
    return False

if not check_password():
    st.stop()

# --- 2. 數據處理與「自動打包」解析引擎 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(new_data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

def parse_text_to_json(raw_text):
    """將人類閱讀格式自動轉換為結構化 JSON"""
    new_data = []
    # 根據「...」類來切分大類
    categories = re.split(r'「(.+?)」類', raw_text)
    
    for i in range(1, len(categories), 2):
        cat_name = categories[i]
        cat_body = categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        
        # 尋找詞根群組 (例如: -fac- (做/製作))
        root_blocks = re.split(r'\n(?=-)', cat_body)
        for block in root_blocks:
            root_info = re.search(r'-([\w/ \-]+)-\s*[\(（](.+?)[\)）]', block)
            if root_info:
                group = {
                    "roots": [r.strip() for r in root_info.group(1).split('/')],
                    "meaning": root_info.group(2).strip(),
                    "vocabulary": []
                }
                # 尋找單字行 (例如: Factory (Fac 做 + tory 場所 = 工廠))
                words = re.findall(r'(\w+)\s*[\(（](.+?)\s*=\s*(.+?)[\)）]', block)
                for w_name, w_logic, w_trans in words:
                    group["vocabulary"].append({
                        "word": w_name.strip(),
                        "breakdown": w_logic.strip(),
                        "definition": w_trans.strip()
                    })
                if group["vocabulary"]:
                    cat_obj["root_groups"].append(group)
        new_data.append(cat_obj)
    return new_data

data = load_data()

# --- 3. 介面導航 ---
st.sidebar.title("🚀 詞根宇宙導航")
mode = st.sidebar.radio("模式：", ["🔍 搜尋解碼", "✍️ 學習測驗", "⚙️ 數據工廠"])

if mode == "🔍 搜尋解碼":
    st.title("🧩 Etymon Decoder")
    search_query = st.text_input("🔍 搜尋單字或詞根...")
    if search_query:
        query = search_query.lower()
        for cat in data:
            for group in cat['root_groups']:
                match_words = [v for v in group['vocabulary'] if query in v['word'].lower()]
                if any(query in r.lower() for r in group['roots']) or match_words:
                    st.write(f"### 詞根: `{' / '.join(group['roots'])}` ({group['meaning']})")
                    for v in group['vocabulary']:
                        st.write(f"**{v['word']}** | `{v['breakdown']}` | {v['definition']}")
                    st.divider()

elif mode == "✍️ 學習測驗":
    st.title("✍️ 詞根解碼挑戰")
    all_words = []
    for cat in data:
        for group in cat['root_groups']:
            for v in group['vocabulary']:
                all_words.append({**v, "root_meaning": group['meaning']})
    
    if all_words:
        if 'q' not in st.session_state:
            st.session_state.q = random.choice(all_words)
            st.session_state.show = False
        
        q = st.session_state.q
        st.subheader(f"單字：:blue[{q['word']}] (提示：{q['root_meaning']})")
        ans_type = st.radio("測驗項目", ["中文含義", "拆解邏輯"])
        if st.button("查看答案"):
            st.session_state.show = True
        if st.session_state.show:
            st.success(f"答案：{q['definition'] if ans_type == '中文含義' else q['breakdown']}")
            if st.button("下一題"):
                st.session_state.q = random.choice(all_words)
                st.session_state.show = False
                st.rerun()

elif mode == "⚙️ 數據工廠":
    st.title("⚙️ 自動化數據打包")
    st.write("直接貼上文字（包含「大類」、詞根及單字公式），系統會自動解析存入資料庫。")
    raw_text = st.text_area("在此貼上文字：", height=300, placeholder="「動作與修飾」類\n-fac- (做/製作)：\nFactory (Fac 做 + tory 場所 = 工廠)")
    
    if st.button("🚀 開始自動解析並儲存"):
        if raw_text:
            try:
                new_parsed_data = parse_text_to_json(raw_text)
                if new_parsed_data:
                    save_data(new_parsed_data)
                    st.success(f"✅ 解析成功！已更新 {len(new_parsed_data)} 個類別。")
                    st.cache_data.clear()
                else:
                    st.error("解析失敗，請確認格式是否正確。")
            except Exception as e:
                st.error(f"解析發生錯誤：{e}")