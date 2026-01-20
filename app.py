import streamlit as st
import json
import os
import re
import random
import requests
import base64
from datetime import datetime

# ==========================================
# 1. 核心設定
# ==========================================
APP_CONFIG = {
    "version": "V1.1",
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
# 2. 數據處理引擎
# ==========================================

def get_github_auth():
    try:
        return st.secrets[APP_CONFIG["github"]["token_secret_key"]], st.secrets[APP_CONFIG["github"]["repo_secret_key"]]
    except:
        st.error("找不到 GitHub Secrets 設定")
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
            "message": f"Auto Update: {filename}",
            "content": base64.b64encode(final_string.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }
        res = requests.put(url, json=payload, headers=headers)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"GitHub 同步出錯：{e}")
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
                    logic_part, def_part = w_logic.split('=', 1) if "=" in w_logic else (w_logic, "待審核")
                    group["vocabulary"].append({"word": w_name.strip(), "breakdown": logic_part.strip(), "definition": def_part.strip()})
                if group["vocabulary"]: cat_obj["root_groups"].append(group)
        if cat_obj["root_groups"]: new_data.append(cat_obj)
    return new_data

# ==========================================
# 3. 介面元件
# ==========================================

def ui_search_page(data):
    st.title("導覽解碼系統")
    query = st.text_input("輸入字根或單字搜尋", placeholder="例如: dict, cap...").lower().strip()
    if query:
        found = False
        for cat in data:
            for group in cat['root_groups']:
                root_match = any(query in r.lower() for r in group['roots'])
                matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()]
                if root_match or matched_v:
                    found = True
                    st.markdown(f"### 基因庫: {cat['category']} ({' / '.join(group['roots'])})")
                    for v in group['vocabulary']:
                        is_target = query in v['word'].lower()
                        with st.expander(f"{'推薦命中: ' if is_target else ''}{v['word']}", expanded=is_target):
                            st.write(f"**拆解：** `{v['breakdown']}`")
                            st.write(f"**含義：** {v['definition']}")
        if not found: st.warning("找不到相關資料")

def ui_quiz_page(data):
    st.title("3D 翻轉閃卡")
    all_words = [{**v, "cat": cat['category']} for cat in data for group in cat['root_groups'] for v in group['vocabulary']]
    if not all_words: return st.info("尚無數據")
    
    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(all_words)
        st.session_state.is_flipped = False
    
    q = st.session_state.flash_q
    is_flipped_class = "flipped" if st.session_state.is_flipped else ""

    flip_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    .flip-card { background-color: transparent; width: 100%; height: 350px; perspective: 1000px; font-family: 'Noto Sans TC', sans-serif; }
    .flip-card-inner { position: relative; width: 100%; height: 100%; transition: transform 0.7s cubic-bezier(0.4, 0, 0.2, 1); transform-style: preserve-3d; }
    .flipped { transform: rotateY(180deg); }
    .flip-card-front, .flip-card-back { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 24px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); background: linear-gradient(135deg, #ffffff 0%, #f9f9fb 100%); border: 1px solid #eee; }
    .flip-card-front { color: #2d3436; }
    .flip-card-back { color: #2d3436; transform: rotateY(180deg); padding: 30px; border: 2px solid #55efc4; }
    </style>
    """
    st.markdown(flip_css, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="flip-card">
      <div class="flip-card-inner {is_flipped_class}">
        <div class="flip-card-front">
          <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 0.8rem; color: #b2bec3;">{q['cat']}</div>
          <h1 style="font-size: 3.5rem; font-weight: 700; margin: 0;">{q['word']}</h1>
          <div style="margin-top:20px; color:#dfe6e9; letter-spacing:1px;">CLICK TO DECODE</div>
        </div>
        <div class="flip-card-back">
          <h2 style="color: #00b894; margin-bottom: 20px; font-weight: 700;">解碼成功</h2>
          <div style="text-align: left; width: 100%;">
            <p style="color: #636e72; margin-bottom: 5px; font-size: 0.9rem;">邏輯拆解</p>
            <p style="background: #f1f2f6; padding: 12px; border-radius: 12px; font-family: monospace; color: #2d3436;">{q['breakdown']}</p>
            <p style="color: #636e72; margin-top: 20px; margin-bottom: 5px; font-size: 0.9rem;">核心含義</p>
            <p style="font-size: 1.6rem; color: #e17055; font-weight: 700;">{q['definition']}</p>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if not st.session_state.is_flipped:
        if st.button("翻轉卡片", use_container_width=True):
            st.session_state.is_flipped = True
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        if col1.button("還不熟", use_container_width=True):
            del st.session_state.flash_q
            st.session_state.is_flipped = False
            st.rerun()
        if col2.button("記住了", use_container_width=True):
            del st.session_state.flash_q
            st.session_state.is_flipped = False
            st.rerun()

def ui_factory_page():
    st.title("數據管理")
    raw_input = st.text_area("數據貼上區", height=250, placeholder="在此輸入 AI 生成的內容...")
    user_name = st.text_input("使用者暱稱", value="Anonymous")
    if st.button("提交數據"):
        parsed = parse_raw_text(raw_input)
        if parsed and save_to_github(parsed, APP_CONFIG["files"]["pending"]):
            save_to_github([{"name": user_name, "date": datetime.now().strftime('%Y-%m-%d'), "type": "Data"}], APP_CONFIG["files"]["contrib"])
            st.success("數據已成功同步")
        else: st.error("操作失敗，請檢查設定")

# ==========================================
# 4. 主程式流程
# ==========================================

def main():
    st.set_page_config(page_title="詞根宇宙", layout="wide")
    data = load_local_json(APP_CONFIG["files"]["db"])
    
    st.sidebar.title("詞根宇宙")
    st.sidebar.caption(f"版本 {APP_CONFIG['version']}")
    
    # 數據統計
    c_count, r_count, w_count = get_stats(data)
    st.sidebar.divider()
    st.sidebar.subheader("數據統計")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("分類", c_count)
    col2.metric("單字量", w_count)
    
    menu = {
        "導覽解碼": lambda: ui_search_page(data),
        "學習測驗": lambda: ui_quiz_page(data),
        "數據管理": ui_factory_page,
        "合作招募": lambda: st.info("聯繫方式：kadowsella@gmail.com")
    }
    choice = st.sidebar.radio("導航選單", list(menu.keys()))
    
    st.sidebar.divider()
    wish = st.sidebar.text_input("單字許願池")
    if st.sidebar.button("送出願望") and wish:
        msg = f"[{datetime.now().strftime('%m-%d %H:%M')}] {wish}\n"
        if save_to_github(msg, APP_CONFIG["files"]["wish"], is_json=False):
            st.sidebar.success("願望已傳送")

    menu[choice]()

if __name__ == "__main__":
    main()
