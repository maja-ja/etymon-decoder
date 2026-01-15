import streamlit as st
import json
import os
from datetime import datetime
import re
import random

# --- 基礎設定與版本 ---
VERSION = "v1.3.0 (2024.01.16)"
DB_FILE = 'etymon_database.json'
CONTRIB_FILE = 'contributors.json'
WISH_FILE = 'wish_list.txt'
PENDING_FILE = 'pending_data.json'
# --- 數據處理函式 ---
def load_json(file_path, default_val):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_val

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_contribution(name, deed, is_anon):
    """更新協作者名單"""
    contributors = load_json(CONTRIB_FILE, [])
    display_name = "Anonymous" if is_anon else name
    
    # 檢查是否已存在
    found = False
    for c in contributors:
        if c['name'] == display_name and not is_anon:
            c['count'] += 1
            c['last_deed'] = deed
            found = True
            break
    
    if not found or is_anon:
        contributors.append({
            "name": display_name,
            "deed": deed,
            "count": 1,
            "date": datetime.now().strftime('%Y-%m-%d')
        })
    save_json(CONTRIB_FILE, contributors)
import re

# --- 數據解析引擎---
def parse_text_to_json(raw_text):
    new_data = []
    # 使用「」或 " " 作為類別切分點
    categories = re.split(r'["「](.+?)["」]類', raw_text)
    
    for i in range(1, len(categories), 2):
        cat_name = categories[i].strip()
        cat_body = categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        
        # 尋找詞根區塊（以 -字根- 開頭）
        root_blocks = re.split(r'\n(?=-)', cat_body)
        for block in root_blocks:
            # 匹配 -root- (meaning)
            root_info = re.search(r'-([\w/ \-]+)-\s*\((.+?)\)', block)
            if root_info:
                group = {
                    "roots": [r.strip() for r in root_info.group(1).split('/')],
                    "meaning": root_info.group(2).strip(),
                    "vocabulary": []
                }
                
                # 匹配：單詞 ( (根)(義)+(根)(義)=含義 )
                # 使用非貪婪匹配捕捉括號內的複雜邏輯
                word_matches = re.findall(r'(\w+)\s*\((.+?)\)', block)
                for w_name, w_logic in word_matches:
                    if "=" in w_logic:
                        logic_part, def_part = w_logic.split('=', 1)
                    else:
                        logic_part, def_part = w_logic, "待審核含義"
                        
                    group["vocabulary"].append({
                        "word": w_name.strip(),
                        "breakdown": logic_part.strip(),
                        "definition": def_part.strip()
                    })
                
                if group["vocabulary"]:
                    cat_obj["root_groups"].append(group)
        
        if cat_obj["root_groups"]:
            new_data.append(cat_obj)
            
    return new_data
# --- 讀取資料庫 (確保在頁面載入時執行) ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 重要：在主程式執行前載入數據
data = load_data()
# --- 模組化區塊模組 ---
def render_section(title, content_func):
    with st.container():
        st.markdown(f"### {title}")
        content_func()
        st.divider()

# --- 頁面配置 ---
st.set_page_config(page_title="詞根宇宙：解碼導航", layout="wide")

# --- 側邊欄 ---
st.sidebar.title("🚀 詞根宇宙")
st.sidebar.caption(f"當前版本：{VERSION}")
mode = st.sidebar.radio("導航選單", ["🔍 導覽解碼", "✍️ 學習測驗", "⚙️ 數據管理", "🏆 榮譽榜", "🤝 合作招募"])
# --- 主介面邏輯 ---

if mode == "🔍 導覽解碼":
    def show_search():
        # 告訴程式使用全域的 data 變數
        global data 
        
        st.write("🔍 輸入單字或字根，立即解析單字基因。")
        query = st.text_input("搜尋關鍵字...", placeholder="例如: dict, cap...", label_visibility="collapsed")
        
        if query:
            q = query.lower().strip()
            found = False
            
            # 確保 data 不是空的才執行
            if data:
                for cat in data:
                    for group in cat['root_groups']:
                        root_match = any(q in r.lower() for r in group['roots'])
                        matched_vocabulary = [v for v in group['vocabulary'] if q in v['word'].lower()]
                        
                        if root_match or matched_vocabulary:
                            found = True
                            st.markdown(f"#### 🧬 詞根家族：`{'/'.join(group['roots'])}` ({group['meaning']})")
                            for v in group['vocabulary']:
                                is_target = q in v['word'].lower()
                                with st.expander(f"{'⭐ ' if is_target else ''}{v['word']}", expanded=is_target):
                                    st.write(f"**拆解：** `{v['breakdown']}`")
                                    st.write(f"**含義：** {v['definition']}")
                
                if not found:
                    st.warning(f"找不到與 '{q}' 相關的結果。")
            else:
                st.error("資料庫目前是空的，請先到數據管理新增資料。")
        else:
            st.info("💡 提示：輸入單字的一部分來查看相關家族。")

    render_section("🔎 導覽解碼系統", show_search)


elif mode == "⚙️ 數據管理":
    def show_factory():
        st.subheader("🛠️ 格式化數據匯入 (待審核隔離區)")
        
        # 1. 格式提示區
        format_hint = """「(名稱1)」類
-字根a-(解釋1/解釋2)
單詞1((字根1)(解釋)+(字根2)(解釋)=含義)

「(名稱2)」類
-字根x-(解釋)
單詞2((字根3)(解釋)+(字根4)(解釋)=含義)"""

        with st.expander("📌 查看標準輸入格式（支援多類別）", expanded=True):
            st.code(format_hint, language="text")
            st.caption("注意：系統會自動將全形括號轉為半形，請放心貼上。")

        # 2. 輸入區
        raw_input = st.text_area(
            "請貼入具格式之文字：", 
            height=300, 
            placeholder=format_hint
        )
        
        c_name = st.text_input("貢獻者名稱", key="factory_name")
        c_deed = st.text_input("本次事蹟", key="factory_deed")
        is_c_anon = st.checkbox("我希望匿名貢獻", key="factory_anon")

        if st.button("🚀 提交至待處理區"):
            if raw_input:
                try:
                    # 先進行符號統一化（全形轉半形）
                    cleaned_input = raw_input.replace('（', '(').replace('）', ')').replace('－', '-').replace('「', '"').replace('」', '"')
                    
                    new_parsed_data = parse_text_to_json(cleaned_input)
                    
                    if new_parsed_data:
                        pending_data = load_json(PENDING_FILE, [])
                        pending_data.extend(new_parsed_data)
                        save_json(PENDING_FILE, pending_data)
                        
                        final_name = "Anonymous" if is_c_anon else (c_name if c_name else "Anonymous")
                        add_contribution(final_name, c_deed, is_c_anon)
                        
                        st.success(f"✅ 已成功隔離儲存 {len(new_parsed_data)} 個類別至待處理區！")
                        st.balloons()
                    else:
                        st.error("❌ 解析失敗：請檢查類別標籤「」與字根格式 - - 是否正確。")
                except Exception as e:
                    st.error(f"⚠️ 解析錯誤：{e}")
            else:
                st.warning("⚠️ 請輸入內容。")

    render_section("⚙️ 數據管理與雙重隔離", show_factory)
elif mode == "✍️ 學習測驗":
    st.title("✍️ 詞根解碼測驗")
    st.info("模式已就緒，請開始挑戰。")
    
    # --- 重要：先定義並填充 all_words ---
    all_words = []
    if data:
        for cat in data:
            for group in cat['root_groups']:
                for v in group['vocabulary']:
                    # 這裡加入 root_meaning 方便測驗時提示
                    all_words.append({**v, "root_meaning": group['meaning']})

    # --- 防呆檢查：如果資料庫完全沒單字 ---
    if not all_words:
        st.warning("⚠️ 資料庫目前沒有單字，請先到「數據管理」匯入資料。")
    else:
        # 確保 random 模組已載入 (import random)
        if 'q' not in st.session_state:
            st.session_state.q = random.choice(all_words)
            st.session_state.show = False
            
        q = st.session_state.q
        st.subheader(f"單字：:blue[{q['word']}]")
        st.write(f"提示（詞根含義）：{q['root_meaning']}")
        
        ans_type = st.radio("你想猜什麼？", ["中文含義", "拆解邏輯"])
        user_ans = st.text_input("輸入你的答案：")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("查看答案"):
                st.session_state.show = True
        
        if st.session_state.show:
            truth = q['definition'] if ans_type == "中文含義" else q['breakdown']
            st.success(f"正確答案：{truth}")
            
            with col2:
                if st.button("下一題"):
                    st.session_state.q = random.choice(all_words)
                    st.session_state.show = False
                    st.rerun()
elif mode == "🏆 榮譽榜":
    def show_contributors():
        st.write("感謝以下夥伴對「詞根宇宙」的貢獻與熱情：")
        contributors = load_json(CONTRIB_FILE, [])
        if contributors:
            # 使用表格呈現
            st.table(contributors)
        else:
            st.info("尚無協作者紀錄，歡迎成為第一位！")
    render_section("🏆 協作者榮譽榜", show_contributors)

elif mode == "🤝 合作招募":
    def recruit_content():
        st.write("我們正在尋找熱愛語言學與 AI 數據整理的夥伴！")
        st.info("""
        **招募角色：**
        1. 數據精煉師：協助校對與擴充詞根 JSON 數據。
        2. 數據代換師：協助轉換至SQLite 或是MySQL。
        3. UI/UX 顧問：優化 Streamlit 介面體驗。
        4. 社群推廣大使：將詞根學習邏輯推廣至 IG/Threads。
        
        **聯繫方式：** 請透過 Instagram/Threads 私訊我或寄信至 kadowsella@gmail.com。
        """)
    render_section("合作招募中心", recruit_content) # 新增合作招募中心

# 頁尾
st.markdown(f"<center style='color:gray; font-size:0.8em;'>詞根宇宙 {VERSION} | Powered by Streamlit & Gemini</center>", unsafe_allow_html=True)
