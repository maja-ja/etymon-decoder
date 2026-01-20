import streamlit as st
import json
import os
import re
import random
import requests
import base64
from datetime import datetime

# ==========================================
# 1. 核心配置
# ==========================================
APP_CONFIG = {
    "version": "V1.5",
    "files": {
        "db": 'etymon_database.json',
        "contrib": 'contributors.json',
        "wish": 'wish_list.txt',
        "pending": 'pending_data.json'
    },
    "github": {
        "token_secret_key": "GITHUB_TOKEN",
        "repo_secret_key": "GITHUB_REPO"
    }
}

# ==========================================
# 2. 核心邏輯
# ==========================================

def get_github_auth():
    try:
        return st.secrets[APP_CONFIG["github"]["token_secret_key"]], st.secrets[APP_CONFIG["github"]["repo_secret_key"]]
    except:
        st.error("認證配置缺失")
        return None, None

def save_to_github(new_data, filename, is_json=True):
    token, repo = get_github_auth()
    if not token or not repo: return False
    try:
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        
        if is_json:
            current_content = []
            if r.status_code == 200:
                content_decoded = base64.b64decode(r.json()["content"]).decode("utf-8")
                try: current_content = json.loads(content_decoded)
                except: current_content = []
            current_content.extend(new_data)
            final_string = json.dumps(current_content, indent=4, ensure_ascii=False)
        else:
            current_string = ""
            if r.status_code == 200:
                current_string = base64.b64decode(r.json()["content"]).decode("utf-8")
            final_string = current_string + new_data

        payload = {
            "message": f"Update: {filename}",
            "content": base64.b64encode(final_string.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }
        res = requests.put(url, json=payload, headers=headers)
        return res.status_code in [200, 201]
    except:
        return False

def load_local_json(file_path, default_val=[]):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return default_val
    return default_val

def get_stats(data):
    total_cats = len(data)
    total_roots = sum(len(cat.get('root_groups', [])) for cat in data)
    total_words = sum(len(g.get('vocabulary', [])) for cat in data for g in cat.get('root_groups', []))
    return total_cats, total_roots, total_words

def parse_raw_text(raw_text):
    new_data = []
    cleaned = raw_text.replace('（', '(').replace('）', ')').replace('－', '-').replace('「', '"').replace('」', '"')
    categories = re.split(r'["\'](.+?)["\']類', cleaned)
    for i in range(1, len(categories), 2):
        cat_name, cat_body = categories[i].strip(), categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        root_blocks = re.split(r'\n(?=-)', cat_body)
        for block in root_blocks:
            root_info = re.search(r'-([\w/ \-]+)-\s*\((.+?)\)', block)
            if root_info:
                group = {"roots": [r.strip() for r in root_info.group(1).split('/')], "meaning": root_info.group(2).strip(), "vocabulary": []}
                word_matches = re.findall(r'(\w+)\s*\((.+?)\)', block)
                for w_name, w_logic in word_matches:
                    logic_part, def_part = w_logic.split('=', 1) if "=" in w_logic else (w_logic, "未定義")
                    group["vocabulary"].append({"word": w_name.strip(), "breakdown": logic_part.strip(), "definition": def_part.strip()})
                if group["vocabulary"]: cat_obj["root_groups"].append(group)
        if cat_obj["root_groups"]: new_data.append(cat_obj)
    return new_data

# ==========================================
# 3. UI 組件
# ==========================================

def ui_search_page(data):
    st.title("字根導覽")
    query = st.text_input("檢索字根或單字", placeholder="例如: scrib, vis...").lower().strip()
    if query:
        found = False
        for cat in data:
            for group in cat['root_groups']:
                root_match = any(query in r.lower() for r in group['roots'])
                matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()]
                if root_match or matched_v:
                    found = True
                    st.markdown(f"**{cat['category']}** ({' / '.join(group['roots'])})")
                    for v in group['vocabulary']:
                        is_target = query in v['word'].lower()
                        with st.expander(f"{v['word']}", expanded=is_target):
                            st.write(f"結構: `{v['breakdown']}`")
                            st.write(f"釋義: {v['definition']}")
        if not found: st.write("未找到匹配項")

def ui_quiz_page(data):
    st.title("記憶卡片")
    all_words = [{**v, "cat": cat['category']} for cat in data for group in cat['root_groups'] for v in group['vocabulary']]
    if not all_words: return st.write("數據庫空缺")
    
    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(all_words)
        st.session_state.is_flipped = False
    
    q = st.session_state.flash_q
    is_flipped_class = "flipped" if st.session_state.is_flipped else ""

    flip_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    .flip-card { background-color: transparent; width: 100%; height: 350px; perspective: 1000px; font-family: 'Inter', sans-serif; }
    .flip-card-inner { position: relative; width: 100%; height: 100%; transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1); transform-style: preserve-3d; }
    .flipped { transform: rotateY(180deg); }
    .flip-card-front, .flip-card-back { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #ffffff; border: 1px solid #e1e4e8; }
    .flip-card-back { transform: rotateY(180deg); padding: 40px; border: 1.5px solid #d1d5da; }
    </style>
    """
    st.markdown(flip_css, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="flip-card">
      <div class="flip-card-inner {is_flipped_class}">
        <div class="flip-card-front">
          <div style="font-size: 0.75rem; color: #888; letter-spacing: 1px;">{q['cat']}</div>
          <h1 style="font-size: 3rem; font-weight: 700; margin: 10px 0; color: #1a1a1a;">{q['word']}</h1>
          <div style="font-size: 0.7rem; color: #ccc; margin-top: 30px;">TAP TO FLIP</div>
        </div>
        <div class="flip-card-back">
          <div style="text-align: left; width: 100%;">
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">結構</div>
            <div style="font-family: monospace; font-size: 1.1rem; color: #333; margin-bottom: 24px;">{q['breakdown']}</div>
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">釋義</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #222;">{q['definition']}</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if not st.session_state.is_flipped:
        if st.button("翻轉", use_container_width=True):
            st.session_state.is_flipped = True
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        if col1.button("標記陌生", use_container_width=True):
            del st.session_state.flash_q
            st.session_state.is_flipped = False
            st.rerun()
        if col2.button("標記熟練", use_container_width=True):
            del st.session_state.flash_q
            st.session_state.is_flipped = False
            st.rerun()

def ui_factory_page():
    st.title("數據管理")
    raw_input = st.text_area("輸入原始文本", height=200, placeholder="貼上待解析內容")
    user_name = st.text_input("貢獻者 ID", value="Anonymous")
    if st.button("提交更新"):
        parsed = parse_raw_text(raw_input)
        if parsed and save_to_github(parsed, APP_CONFIG["files"]["pending"]):
            st.toast("數據已排隊等候同步")
        else: st.error("提交未成功")

# ==========================================
# 4. 主程序
# ==========================================

def main():
    st.set_page_config(page_title="Etymon", layout="wide")
    data = load_local_json(APP_CONFIG["files"]["db"])
    
    st.sidebar.title("Etymon")
    st.sidebar.caption(f"Build {APP_CONFIG['version']}")
    
    c_count, r_count, w_count = get_stats(data)
    st.sidebar.divider()
    st.sidebar.write("**統計數據**")
    st.sidebar.text(f"分類: {c_count}")
    st.sidebar.text(f"單字: {w_count}")
    
    menu = {
        "字根導覽": lambda: ui_search_page(data),
        "記憶卡片": lambda: ui_quiz_page(data),
        "數據管理": ui_factory_page,
        "關於項目": lambda: st.write("Etymon Decoder Project v1.1")
    }
    choice = st.sidebar.radio("選單", list(menu.keys()), label_visibility="collapsed")
    
    st.sidebar.divider()
    wish = st.sidebar.text_input("詞彙需求", placeholder="輸入想查的詞")
    if st.sidebar.button("提交") and wish:
        msg = f"[{datetime.now().strftime('%m%d %H%M')}] {wish}\n"
        save_to_github(msg, APP_CONFIG["files"]["wish"], is_json=False)
        st.sidebar.write("需求已紀錄")

    menu[choice]()

if __name__ == "__main__":
    main()
