import streamlit as st
import json
import os
import re
import random
import requests
import base64
from datetime import datetime

# ==========================================
# 1. 核心設定 (以後改這裡就好)
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
# 2. 數據處理工具 (引擎部分)
# ==========================================

def get_github_auth():
    """取得 GitHub 認證資訊"""
    try:
        return st.secrets[APP_CONFIG["github"]["token_secret_key"]], st.secrets[APP_CONFIG["github"]["repo_secret_key"]]
    except:
        st.error("❌ 找不到 GitHub Secrets 設定 (GITHUB_TOKEN / GITHUB_REPO)")
        return None, None

def save_to_github(new_data, filename, is_json=True):
    """通用 GitHub 同步函式"""
    token, repo = get_github_auth()
    if not token or not repo: return False

    try:
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

        # 抓取舊檔案 SHA 與內容
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

        # 推送更新
        payload = {
            "message": f"🤖 自動更新: {filename}",
            "content": base64.b64encode(final_string.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }
        res = requests.put(url, json=payload, headers=headers)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"GitHub 同步出錯：{e}")
        return False

def load_local_json(file_path, default_val=[]):
    """讀取本地端 JSON 檔案"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return default_val
    return default_val

def parse_raw_text(raw_text):
    """將 AI 格式文字解析為 JSON 結構"""
    new_data = []
    cleaned = raw_text.replace('（', '(').replace('）', ')').replace('－', '-').replace('「', '"').replace('」', '"')
    categories = re.split(r'["\'](.+?)["\']類', cleaned)
    
    for i in range(1, len(categories), 2):
        cat_name = categories[i].strip()
        cat_body = categories[i+1]
        cat_obj = {"category": cat_name, "root_groups": []}
        root_blocks = re.split(r'\n(?=-)', cat_body)
        
        for block in root_blocks:
            root_info = re.search(r'-([\w/ \-]+)-\s*\((.+?)\)', block)
            if root_info:
                group = {
                    "roots": [r.strip() for r in root_info.group(1).split('/')],
                    "meaning": root_info.group(2).strip(),
                    "vocabulary": []
                }
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

# ==========================================
# 3. 介面元件 (UI Components)
# ==========================================

def ui_search_page(data):
    st.title("🔍 導覽解碼系統")
    
    # 隨機推薦
    if 'preview_words' not in st.session_state:
        all_v = []
        for cat in data:
            for group in cat['root_groups']:
                for v in group['vocabulary']:
                    all_v.append({**v, "cat": cat['category'], "roots": group['roots']})
        st.session_state.preview_words = random.sample(all_v, min(len(all_v), 3)) if all_v else []

    # 推薦卡片
    cols = st.columns(3)
    for i, word in enumerate(st.session_state.preview_words):
        with cols[i]:
            st.markdown(f"""<div style="border:1px solid #ddd; border-radius:8px; padding:10px; background:#f9f9f9;">
                <h4 style="margin:0; color:#007BFF;">{word['word']}</h4>
                <small>{word['cat']} | {'/'.join(word['roots'])}</small>
            </div>""", unsafe_allow_html=True)
    
    if st.button("🔄 換一批推薦"):
        del st.session_state.preview_words
        st.rerun()

    st.divider()

    # 搜尋邏輯
    query = st.text_input("輸入字根或單字搜尋", placeholder="例如: dict, photo...").lower().strip()
    if query:
        found = False
        for cat in data:
            for group in cat['root_groups']:
                root_match = any(query in r.lower() for r in group['roots'])
                matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()]
                
                if root_match or matched_v:
                    found = True
                    st.markdown(f"### 🧬 {cat['category']} (`{' / '.join(group['roots'])}`)")
                    for v in group['vocabulary']:
                        is_target = query in v['word'].lower()
                        with st.expander(f"{'⭐ ' if is_target else ''}{v['word']}", expanded=is_target):
                            st.write(f"**拆解：** `{v['breakdown']}`")
                            st.write(f"**含義：** {v['definition']}")
        if not found: st.warning("找不到相關資料。")

def get_card_style(category_name):
    """根據類別名稱決定顏色"""
    colors = {
        "心靈": "#FFD1DC", "科技": "#E0F7FA", 
        "感知": "#FFF9C4", "動作": "#DCEDC8"
    }
    # 如果沒匹配到，預設灰色
    bg_color = next((v for k, v in colors.items() if k in category_name), "#F5F5F5")
    
    return f"""
    <div style="
        background-color: {bg_color};
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #333;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
    ">
    """
def ui_factory_page():
    st.title("⚙️ 數據管理")
    st.info("請將 AI 生成的標準格式貼在下方，系統會自動處理並同步至 GitHub。")
    
    with st.expander("📌 格式範本與提示詞", expanded=False):
        st.code("「（分類）」類\n-字根-(含義)\n單字((前綴)+(字根)=總義)", language="text")
    
    raw_input = st.text_area("數據貼上區", height=250)
    user_name = st.text_input("你的暱稱", value="Anonymous")
    
    if st.button("🚀 提交數據"):
        parsed_data = parse_raw_text(raw_input)
        if parsed_data:
            if save_to_github(parsed_data, APP_CONFIG["files"]["pending"]):
                # 同步貢獻名單
                contrib = [{"name": user_name, "date": datetime.now().strftime('%Y-%m-%d'), "type": "Data"}]
                save_to_github(contrib, APP_CONFIG["files"]["contrib"])
                st.success("數據已成功送往 GitHub 隔離區！")
                st.balloons()
            else:
                st.error("同步失敗，請檢查 Secrets 設定。")
        else:
            st.error("解析錯誤，請確認輸入格式。")
def ui_note_page():
    st.title("📓 我的筆記本")
    st.write("這裡是你的私人單字區...")
def get_stats(data):
    """計算資料庫統計數據"""
    total_cats = len(data)
    total_roots = 0
    total_words = 0
    
    for cat in data:
        total_roots += len(cat.get('root_groups', []))
        for group in cat.get('root_groups', []):
            total_words += len(group.get('vocabulary', []))
            
    return total_cats, total_roots, total_words

# ==========================================
# 4. 主程式流程 (Main Entry)
# ==========================================

def main():
    st.set_page_config(page_title="詞根宇宙", layout="wide")
    
    # 載入數據
    data = load_local_json(APP_CONFIG["files"]["db"])

    # 側邊欄導覽
    st.sidebar.title("🚀 詞根宇宙")
    st.sidebar.caption(f"Version {APP_CONFIG['version']}")
    data = load_local_json(APP_CONFIG["files"]["db"])
    
    # 計算統計
    c_count, r_count, w_count = get_stats(data)

    # 在側邊欄顯示漂亮的指標
    st.sidebar.divider()
    st.sidebar.subheader("📊 宇宙概況")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("分類", c_count)
    col2.metric("單字量", w_count)
    st.sidebar.caption(f"由 {r_count} 組核心字根建構而成")
    menu = {
        "🔍 導覽解碼": lambda: ui_search_page(data),
        "✍️ 學習測驗": lambda: ui_quiz_page(data),
        "⚙️ 數據管理": ui_factory_page,
        "📓 筆記本": ui_note_page,
        "🤝 合作招募": lambda: st.info("聯繫方式：kadowsella@gmail.com")
    }
    
    choice = st.sidebar.radio("導航選單", list(menu.keys()))
    
    # 側邊欄許願池
    st.sidebar.divider()
    wish = st.sidebar.text_input("🎯 單字許願池")
    if st.sidebar.button("送出願望"):
        msg = f"[{datetime.now().strftime('%m-%d %H:%M')}] {wish}\n"
        if save_to_github(msg, APP_CONFIG["files"]["wish"], is_json=False):
            st.sidebar.success("願望已傳達！")

    # 執行頁面函式
    menu[choice]()

if __name__ == "__main__":
    main()
