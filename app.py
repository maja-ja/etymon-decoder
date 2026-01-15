import streamlit as st
import json
import os
from datetime import datetime
import re
import random
import requests
import base64

# --- 基礎設定與版本 ---
VERSION = "v1.3.1 (2024.01.16)"
DB_FILE = 'etymon_database.json'
CONTRIB_FILE = 'contributors.json'
WISH_FILE = 'wish_list.txt'
PENDING_FILE = 'pending_data.json'


# --- 數據處理函式 ---
def save_to_github(new_data, filename):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {"Authorization": f"token {token}"}

    # 1. 先抓取 GitHub 上舊檔案的內容與 SHA (GitHub 規定更新檔案必須要有 SHA)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    
    # 2. 合併資料
    current_content = []
    if r.status_code == 200:
        content_decoded = base64.b64decode(r.json()["content"]).decode("utf-8")
        current_content = json.loads(content_decoded)
    
    current_content.extend(new_data)
    new_json_content = json.dumps(current_content, indent=4, ensure_ascii=False)

    # 3. 推送回去
    payload = {
        "message": f"Update {filename} via Etymon Universe App",
        "content": base64.b64encode(new_json_content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code == 200 or res.status_code == 201
def load_json(file_path, default_val):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return default_val
    return default_val

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_contribution(name, deed, is_anon):
    contributors = load_json(CONTRIB_FILE, [])
    display_name = "Anonymous" if is_anon else (name if name else "Anonymous")
    
    found = False
    if display_name != "Anonymous":
        for c in contributors:
            if c['name'] == display_name:
                c['count'] += 1
                c['deed'] = deed # 更新最新事蹟
                found = True
                break
    
    if not found:
        contributors.append({
            "name": display_name,
            "deed": deed,
            "count": 1,
            "date": datetime.now().strftime('%Y-%m-%d')
        })
    save_json(CONTRIB_FILE, contributors)

# --- 數據解析引擎 ---
def parse_text_to_json(raw_text):
    new_data = []
    # 統一標點符號：全形轉半形
    cleaned = raw_text.replace('（', '(').replace('）', ')').replace('－', '-').replace('「', '"').replace('」', '"')
    
    # 分割類別
    categories = re.split(r'["\'](.+?)["\']類', cleaned)
    for i in range(1, len(categories), 2):
        cat_name = categories[i].strip()
        cat_body = categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        
        # 分割詞根區塊
        root_blocks = re.split(r'\n(?=-)', cat_body)
        for block in root_blocks:
            root_info = re.search(r'-([\w/ \-]+)-\s*\((.+?)\)', block)
            if root_info:
                group = {
                    "roots": [r.strip() for r in root_info.group(1).split('/')],
                    "meaning": root_info.group(2).strip(),
                    "vocabulary": []
                }
                # 匹配單詞與邏輯：單詞((根)(義)+(根)(義)=含義)
                word_matches = re.findall(r'(\w+)\s*\((.+?)\)', block)
                for w_name, w_logic in word_matches:
                    logic_part, def_part = w_logic.split('=', 1) if "=" in w_logic else (w_logic, "待審核")
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

# 預載數據
data = load_json(DB_FILE, [])

# --- 模組化區塊 ---
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

# 側邊欄隔離區：許願池
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 零散單字許願")
wish_word = st.sidebar.text_input("想要新增的單字", placeholder="例如: Metaphor")
is_wish_anon = st.sidebar.checkbox("匿名許願")
if st.sidebar.button("提交願望"):
    if wish_word:
        user = "Anonymous" if is_wish_anon else "User"
        with open(WISH_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d')}] {user}: {wish_word}\n")
        st.sidebar.success("已加入待辦清單")

# --- 主介面邏輯 ---

if mode == "🔍 導覽解碼":
    def show_search():
        query = st.text_input("🔍 搜尋單字或詞根...", placeholder="輸入關鍵字...")
        if query:
            q = query.lower().strip()
            found = False
            for cat in data:
                for group in cat['root_groups']:
                    root_match = any(q in r.lower() for r in group['roots'])
                    matched_v = [v for v in group['vocabulary'] if q in v['word'].lower()]
                    if root_match or matched_v:
                        found = True
                        st.markdown(f"#### 🧬 {cat['category']} | `{' / '.join(group['roots'])}` ({group['meaning']})")
                        for v in group['vocabulary']:
                            is_target = q in v['word'].lower()
                            with st.expander(f"{'⭐ ' if is_target else ''}{v['word']}", expanded=is_target):
                                st.write(f"**拆解：** `{v['breakdown']}`")
                                st.write(f"**含義：** {v['definition']}")
            if not found: st.warning("未找到相關結果")
    render_section("導覽解碼系統", show_search)

elif mode == "⚙️ 數據管理":
    def show_factory():
        st.info("📦 此處提交的正式數據將先進入隔離區。")
        
        hint = """「(名稱1)」類
-(字根a)-(解釋)
單詞1((字根1)(義)+(字根2)(義)=含義)

「(名稱2)」類
-(字根b)-(解釋)
單詞2((字根3)(義)+(字根4)(義)=含義)"""
        
        with st.expander("📌 查看標準輸入格式提示", expanded=True):
            st.code(hint, language="text")

        raw_input = st.text_area("數據貼上區", height=300, placeholder="請依上述格式輸入...")
        c_name = st.text_input("貢獻者名稱")
        c_deed = st.text_input("本次事蹟")
        is_c_anon = st.checkbox("匿名貢獻")

        if st.button("🚀 提交至待處理隔離區"):
            if raw_input:
                parsed = parse_text_to_json(raw_input)
                if parsed:
                    pending = load_json(PENDING_FILE, [])
                    pending.extend(parsed)
                    save_json(PENDING_FILE, pending)
                    add_contribution(c_name, c_deed, is_c_anon)
                    st.success("數據已存入待處理區！")
                    st.balloons()
                else:
                    st.error("解析失敗，請檢查括號與類別標記。")
    render_section("數據工廠與隔離區", show_factory)

elif mode == "✍️ 學習測驗":
    all_words = []
    for cat in data:
        for group in cat['root_groups']:
            for v in group['vocabulary']:
                all_words.append({**v, "root_meaning": group['meaning']})

    if not all_words:
        st.warning("資料庫暫無內容。")
    else:
        if 'q' not in st.session_state:
            st.session_state.q = random.choice(all_words)
            st.session_state.show = False
        
        q = st.session_state.q
        st.subheader(f"挑戰單字：:blue[{q['word']}]")
        st.caption(f"提示：詞根含義為 「{q['root_meaning']}」")
        
        ans_type = st.radio("測驗類型", ["中文含義", "拆解邏輯"])
        if st.button("查看答案"): st.session_state.show = True
        
        if st.session_state.show:
            st.success(f"答案：{q['definition'] if ans_type == '中文含義' else q['breakdown']}")
            if st.button("下一題"):
                st.session_state.q = random.choice(all_words)
                st.session_state.show = False
                st.rerun()

elif mode == "🏆 榮譽榜":
    render_section("協作者榮譽榜", lambda: st.table(load_json(CONTRIB_FILE, [])))
elif mode == "🤝 合作招募":
    def recruit_content():
        st.write("我們正在尋找熱愛語言學與 AI 數據整理的夥伴！")
        st.info("""
        
        
        **聯繫方式：** 請透過 Instagram/Threads 私訊我或寄信至 kadowsella@gmail.com。
        """)
    render_section("合作招募中心", recruit_content) # 新增合作招募中心


st.markdown(f"<center style='color:gray; font-size:0.8em;'>詞根宇宙 {VERSION}</center>", unsafe_allow_html=True)
