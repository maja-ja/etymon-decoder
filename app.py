import streamlit as st
import json
import os
from datetime import datetime

# --- 基礎設定與版本 ---
VERSION = "v1.3.0 (2024.01.16)"
DB_FILE = 'etymon_database.json'
CONTRIB_FILE = 'contributors.json'
WISH_FILE = 'wish_list.txt'

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

# 許願池
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 希望的單字")
wish_name = st.sidebar.text_input("您的稱呼 (可留空)", key="wish_name")
wish_word = st.sidebar.text_input("想要新增的單字", key="wish_word")
is_wish_anon = st.sidebar.checkbox("匿名上傳", key="wish_anon")

if st.sidebar.button("提交需求"):
    if wish_word:
        final_name = "Anonymous" if is_wish_anon else (wish_name if wish_name else "Anonymous")
        with open(WISH_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d')}] {final_name}: {wish_word}\n")
        st.sidebar.success("願望已收錄！")

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
        st.write("將 AI 產出的格式貼上以自動打包。")
        raw_input = st.text_area("數據貼上區", height=200)
        c_name = st.text_input("貢獻者名稱")
        c_deed = st.text_input("本次事蹟 (如：新增動作類詞根)")
        is_c_anon = st.checkbox("我希望匿名貢獻")
        
        if st.button("🚀 開始打包並記錄貢獻"):
            if raw_input:
                # 1. 執行數據解析 (將文字轉為結構化 JSON)
                try:
                    new_parsed_data = parse_text_to_json(raw_input)
                    
                    if new_parsed_data:
                        # 2. 儲存至資料庫
                        # 這裡建議採取「附加」而非覆蓋，或是讀取現有的再合併
                        existing_data = load_data()
                        # 簡易合併邏輯：將新解析的類別加入舊數據中
                        existing_data.extend(new_parsed_data)
                        save_data(existing_data)
                        
                        # 3. 處理協作者名稱與記錄貢獻
                        # 如果勾選匿名，強行將名稱設為 Anonymous
                        final_contributor_name = "Anonymous" if is_c_anon else (c_name if c_name else "Anonymous")
                        
                        add_contribution(final_contributor_name, c_deed, is_c_anon)
                        
                        st.success(f"✅ 成功打包！已記錄來自 {final_contributor_name} 的貢獻。")
                        st.balloons() # 慶祝成功
                        st.cache_data.clear() # 清除快取以顯示最新搜尋結果
                    else:
                        st.error("❌ 解析失敗：請檢查貼上的文字格式是否符合規範。")
                except Exception as e:
                    st.error(f"⚠️ 解析過程中發生錯誤：{e}")
            else:
                st.warning("⚠️ 請先在上方貼入單字數據文字。")
    render_section("⚙️ 數據工廠", show_factory)
elif mode == "✍️ 學習測驗":
    st.title("✍️ 詞根解碼測驗")
    st.info("模式已就緒，請開始挑戰。")
    all_words = []
    for cat in data:
        for group in cat['root_groups']:
            for v in group['vocabulary']:
                all_words.append({**v, "root_meaning": group['meaning']}) #

    if 'q' not in st.session_state:
        st.session_state.q = random.choice(all_words)
        st.session_state.show = False
    q = st.session_state.q
    st.subheader(f"單字：:blue[{q['word']}]")
    
    ans_type = st.radio("你想猜什麼？", ["中文含義", "拆解邏輯"])
    user_ans = st.text_input("輸入答案：")
    
    if st.button("查看答案"):
        st.session_state.show = True
    
    if st.session_state.show:
        truth = q['definition'] if ans_type == "中文含義" else q['breakdown']
        st.info(f"正確答案：{truth}")
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
