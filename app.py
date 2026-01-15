import streamlit as st
import json
import random
import os
import re
from datetime import datetime

# --- 基礎設定 ---
DB_FILE = 'etymon_database.json'
WISH_FILE = 'wish_list.txt'
VERSION = "v1.2.0 (2024.01.16)"

# --- 1. 數據處理功能 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(new_data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

def parse_text_to_json(raw_text):
    """解析自定義格式為結構化 JSON"""
    new_data = []
    categories = re.split(r'「(.+?)」類', raw_text)
    for i in range(1, len(categories), 2):
        cat_name = categories[i]
        cat_body = categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        root_blocks = re.split(r'\n(?=-)', cat_body)
        for block in root_blocks:
            root_info = re.search(r'-([\w/ \-]+)-\s*[\(（](.+?)[\)）]', block)
            if root_info:
                group = {
                    "roots": [r.strip() for r in root_info.group(1).split('/')],
                    "meaning": root_info.group(2).strip(),
                    "vocabulary": []
                }
                # 支援多個括號組成的複雜拆解格式
                words = re.findall(r'(\w+)\s*[\(（](.+?)[\)）]', block)
                for w_name, w_logic in words:
                    # 判斷是否為真正的拆解公式（含有 = 或多個括號組合）
                    if "=" in w_logic or "+" in w_logic:
                        parts = w_logic.split('=')
                        logic = parts[0].strip()
                        def_text = parts[1].strip() if len(parts) > 1 else "待定義"
                        group["vocabulary"].append({"word": w_name, "breakdown": logic, "definition": def_text})
                if group["vocabulary"]:
                    cat_obj["root_groups"].append(group)
        new_data.append(cat_obj)
    return new_data

# --- 2. 模組化區塊 (方便未來擴充) ---
def render_section(title, content_func):
    """新增區塊模組：統一標題樣式與容器內容"""
    with st.container():
        st.markdown(f"### 🛡️ {title}")
        content_func()
        st.divider()

# --- 3. 介面設定 ---
st.set_page_config(page_title="詞根宇宙：解碼導航", layout="wide")
data = load_data()

# 側邊欄：導航與版本資訊
st.sidebar.title("🚀 詞根宇宙導航")
st.sidebar.caption(f"版本號：{VERSION}") # 新增版本號提示
st.sidebar.markdown("---")

mode = st.sidebar.radio("切換模式：", ["🔍 導覽解碼", "✍️ 學習測驗", "⚙️ 數據管理", "🤝 合作招募"])

# 側邊欄：新增「希望的單字」輸入框
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 許願池")
wish_word = st.sidebar.text_input("輸入您希望新增的單字：", placeholder="例如: Metaphor")
if st.sidebar.button("提交願望"):
    if wish_word:
        with open(WISH_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {wish_word}\n")
        st.sidebar.success("願望已記錄！")

# --- 4. 功能邏輯 ---

if mode == "🔍 導覽解碼":
    def search_content():
        query = st.text_input("🔍 搜尋單字或詞根...")
        if query:
            q = query.lower()
            for cat in data:
                for group in cat['root_groups']:
                    match = [v for v in group['vocabulary'] if q in v['word'].lower()]
                    if any(q in r.lower() for r in group['roots']) or match:
                        st.write(f"#### 詞根: `{' / '.join(group['roots'])}` ({group['meaning']})")
                        for v in group['vocabulary']:
                            st.write(f"**{v['word']}** | `{v['breakdown']}` | {v['definition']}")
    render_section("導覽解碼系統", search_content)

elif mode == "✍️ 學習測驗":
    def quiz_content():
        st.write("挑戰單字結構與含義記憶。")
        # (保留之前的測驗邏輯)
    render_section("詞根解碼挑戰", quiz_content)

elif mode == "⚙️ 數據管理":
    def management_content():
        st.markdown("將單字以指定格式貼上，系統將自動打包。")
        raw_text = st.text_area("資料匯入區：", height=250, placeholder="「（名稱）」類\n-字根a- (解釋)\n單詞 ( (根)(義) + (根)(義) = 含義 )")
        if st.button("🚀 執行自動化打包"):
            if raw_text:
                parsed = parse_text_to_json(raw_text)
                save_data(parsed)
                st.success("數據已成功儲存！")
    render_section("數據工廠", management_content)

elif mode == "🤝 合作招募":
    def recruit_content():
        st.write("我們正在尋找熱愛語言學與 AI 數據整理的夥伴！")
        st.info("""
        **招募角色：**
        1. 數據精煉師：協助校對與擴充詞根 JSON 數據。
        2. UI/UX 顧問：優化 Streamlit 介面體驗。
        3. 社群推廣大使：將詞根學習邏輯推廣至 IG/Threads。
        
        **聯繫方式：** 請透過 Instagram 私訊我或寄信至 [您的聯絡信箱]。
        """)
    render_section("合作招募中心", recruit_content) # 新增合作招募中心

# 頁尾資訊
st.markdown(f"<p style='text-align: center; color: gray;'>詞根宇宙 {VERSION} | 以邏輯解構語言</p>", unsafe_allow_html=True)
