import streamlit as st
import json
import random
import os
import re

DB_FILE = 'etymon_database.json'

# --- 1. 自動解析引擎 (關鍵功能) ---
def parse_raw_text(raw_text):
    """
    將人類閱讀的格式自動轉為結構化 JSON
    """
    new_data = []
    # 切分大類
    categories = re.split(r'「(.+?)」類', raw_text)
    
    for i in range(1, len(categories), 2):
        cat_name = categories[i]
        cat_content = categories[i+1]
        
        cat_obj = {"category": cat_name, "root_groups": []}
        
        # 尋找詞根區塊 (例如: -fac- / -fec- ...)
        root_blocks = re.split(r'\n(?=-)', cat_content)
        for block in root_blocks:
            root_match = re.search(r'-([\w/ \-]+)-\s*[\(（](.+?)[\)）]', block)
            if root_match:
                group = {
                    "roots": [r.strip() for r in root_match.group(1).split('/')],
                    "meaning": root_match.group(2).strip(),
                    "vocabulary": []
                }
                # 尋找單字行 (例如: Factory (Fac 做 + tory 場所 = 工廠))
                words = re.findall(r'(\w+[\-\w]*)\s*[\(（](.+?)\s*=\s*(.+?)[\)）]', block)
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

# --- 2. 基礎功能 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 3. 頁面邏輯 ---
st.set_page_config(page_title="詞根宇宙：自動解碼版", layout="wide")

# 密碼鎖 (保留你要求的密碼功能)
if "authenticated" not in st.session_state:
    st.title("🔐 詞根宇宙私有訪問")
    pwd = st.text_input("輸入訪問密碼：", type="password")
    if st.button("登入"):
        if pwd == "8888":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
    st.stop()

data = load_data()
tab1, tab2, tab3 = st.tabs(["🔍 搜尋解碼", "✍️ 學習測驗", "⚙️ 數據工廠"])

with tab1:
    st.title("🧩 詞根搜尋")
    query = st.text_input("輸入單字/詞根：")
    if query:
        q = query.lower()
        for cat in data:
            for group in cat['root_groups']:
                match = [v for v in group['vocabulary'] if q in v['word'].lower()]
                if any(q in r.lower() for r in group['roots']) or match:
                    st.success(f"詞根：{'/'.join(group['roots'])} | 含義：{group['meaning']}")
                    for v in group['vocabulary']:
                        st.write(f"**{v['word']}** → `{v['breakdown']}` | {v['definition']}")

with tab2:
    st.title("✍️ 自我測驗")
    # ... (此處保留之前的 random.choice 測驗邏輯) ...

with tab3:
    st.title("⚙️ 數據工廠 (自動打包)")
    st.markdown("### 1. 直接貼上文字")
    raw_input = st.text_area("直接貼上文字格式 (例如：-fac- 做...)", height=300)
    
    if st.button("🚀 開始自動解析並儲存"):
        if raw_input:
            structured_data = parse_raw_text(raw_input)
            save_data(structured_data)
            st.success("解析成功！數據已打包並存入資料庫。")
            st.cache_data.clear()
    
    st.markdown("---")
    st.markdown("### 2. 進階：手動校對 JSON")
    st.json(data)