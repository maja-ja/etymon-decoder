import streamlit as st
import json
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 核心配置與資料載入 (移除語音相關 import)
# ==========================================

SHEET_ID = '1Gs0FX7c8bUQTnSytX1EqjMLATeVc30GmdjSOYW_sYsQ'
GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

@st.cache_data(ttl=600) # 快取減少 Stop 出現機率
def load_db():
    import string
    ALPHABET = list(string.ascii_uppercase)
    BLOCK_MAP = {letter: i * 11 for i, letter in enumerate(ALPHABET)}
    
    try:
        raw_df = pd.read_csv(GSHEET_URL)
        if raw_df.empty: return []
    except Exception as e:
        st.error(f"讀取試算表失敗: {e}")
        return []

    structured_data = []
    for letter, start_idx in BLOCK_MAP.items():
        if start_idx + 3 >= len(raw_df.columns): continue
        try:
            df_part = raw_df.iloc[:, start_idx:start_idx+9].copy()
            df_part.columns = ['category', 'roots', 'meaning', 'word', 'breakdown', 'definition', 'phonetic', 'example', 'translation']
            df_part = df_part[df_part['word'].notna()]
            df_part = df_part[df_part['word'].astype(str).str.lower() != 'word']
            
            if df_part.empty: continue

            sub_cats = []
            for cat_name, cat_group in df_part.groupby('category'):
                root_groups = []
                for (roots, meaning), group_df in cat_group.groupby(['roots', 'meaning']):
                    vocabulary = []
                    for _, row in group_df.iterrows():
                        word_val = str(row['word']).strip()
                        if word_val and word_val.lower() != 'nan':
                            vocabulary.append({
                                "word": word_val,
                                "breakdown": str(row['breakdown']),
                                "definition": str(row['definition']),
                                "phonetic": str(row['phonetic']),
                                "example": str(row['example']),
                                "translation": str(row['translation'])
                            })
                    if vocabulary:
                        root_groups.append({
                            "roots": [r.strip() for r in str(roots).split('/')],
                            "meaning": str(meaning),
                            "vocabulary": vocabulary
                        })
                if root_groups:
                    sub_cats.append({"name": str(cat_name), "root_groups": root_groups})
            if sub_cats:
                structured_data.append({"letter": letter, "sub_categories": sub_cats})
        except: continue
    return structured_data

# ==========================================
# 2. UI 組件 (已完全移除喇叭/語音邏輯)
# ==========================================
def render_word_card(v, title="General", theme_color="#1E88E5"):
    """
    統一的單字卡渲染函式
    v: 單字資料字典
    title: 來源頁面標題 (用於判斷顏色與 Key)
    theme_color: 預設卡片標題顏色
    """
    with st.container(border=True):
        col_w, col_p, col_f = st.columns([3, 0.8, 0.8]) # 預留回報空間
        
        with col_w:
            # 根據標題判斷顏色 (法律區為金色)
            display_color = "#FFD700" if "法律" in title else theme_color
            st.markdown(f'<div style="font-size: 2.2em; font-weight: bold; color: {display_color}; line-height:1.2;">{v["word"]}</div>', unsafe_allow_html=True)
            
            if v.get('phonetic') and str(v['phonetic']) != "nan": 
                st.caption(f"/{v['phonetic'].strip('/')}/")
                
        with col_p:
            # 修正後的唯一 Key 生成
            btn_key = f"spk_{v['word']}_{title}_{random.randint(0, 100000)}"
            if st.button("🔊", key=btn_key, help="播放發音"): 
                speak(v['word'])
        
        with col_f:
            # 呼叫回報組件
            if 'ui_feedback_component' in globals():
                ui_feedback_component(v['word'])
        
        # 構造拆解與定義
        st.markdown(f"""
            <div style="margin-top: 10px;">
                <span style="color: #888;">構造拆解：</span>
                <code style="font-size: 1.2em; color: #FFD700; background: #333; padding: 2px 8px; border-radius: 5px;">{v['breakdown']}</code>
            </div>
            <div style="margin-top: 8px; font-size: 1.1em;">
                <b>定義：</b> {v['definition']}
            </div>
        """, unsafe_allow_html=True)
        
        if v.get('example') and str(v['example']) != "nan":
            with st.expander("查看例句"):
                st.write(v['example'])
                if v.get('translation') and str(v['translation']) != "nan":
                    st.caption(f"({v['translation']})")
def ui_quiz_page(data):
    st.title("學習區 (Flashcards)")
    pool = []
    for block in data:
        for sub in block.get('sub_categories', []):
            for group in sub.get('root_groups', []):
                for v in group.get('vocabulary', []):
                    item = v.copy()
                    item['cat'] = sub['name']
                    pool.append(item)
    
    if not pool:
        st.warning("資料庫為空。")
        return

    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False

    q = st.session_state.flash_q
    st.info(f"📍 分類：{q['cat']}")
    st.markdown(f"""<div style="text-align: center; padding: 40px; border: 2px solid #1E88E5; border-radius: 20px; background: #f9f9f9;">
                    <h1 style="font-size: 3.5em; color: #1E88E5; margin: 0;">{q['word']}</h1></div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("👀 顯示答案", use_container_width=True):
            st.session_state.flipped = True
    with c2:
        if st.button("➡️ 下一個單字", use_container_width=True):
            st.session_state.flash_q = random.choice(pool)
            st.session_state.flipped = False
            st.rerun()

    if st.session_state.get('flipped'):
        st.markdown("---")
        st.success(f"**拆解：** {q['breakdown']}")
        st.write(f"**解釋：** {q['definition']}")
def ui_domain_page(domain_data, title, theme_color, bg_color):
    st.title(title)
    if not domain_data:
        st.info("目前資料庫中尚未建立相關分類。")
        return

    # 提取字根
    root_map = {}
    for cat in domain_data:
        for group in cat.get('root_groups', []):
            label = f"{'/'.join(group['roots'])} ({group['meaning']})"
            if label not in root_map: root_map[label] = group
    
    selected_label = st.selectbox("選擇要複習的字根", sorted(root_map.keys()), key=f"sel_{title}")
    
    if selected_label:
        group = root_map[selected_label]
        for v in group.get('vocabulary', []):
            # 直接呼叫統一的渲染函式，傳入當前的 title
            render_word_card(v, title=title, theme_color=theme_color)
# ==========================================
# 3. 主程序入口
# ==========================================

def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    data = load_db()
    
    # 側邊欄
    st.sidebar.title("Etymon Decoder")
    menu = st.sidebar.radio("導航選單", ["搜尋與瀏覽", "字根區", "學習區", "醫學區", "法律區", "管理區"])
    
    if st.sidebar.button("🔄 刷新雲端資料"):
        st.cache_data.clear()
        st.rerun()

    # 頁面邏輯
    if menu == "搜尋與瀏覽":
        st.title("🔍 全域單字搜尋")
        query = st.text_input("輸入關鍵字 (單字/中文/字根)").strip().lower()
        if query:
            count = 0
            for b in data:
                for s in b['sub_categories']:
                    for g in s['root_groups']:
                        for v in g['vocabulary']:
                            # 比對單字、定義或翻譯
                            if query in v['word'].lower() or query in v['definition'].lower() or query in v.get('translation','').lower():
                                with st.expander(f"📖 {v['word']} (分類: {s['name']})"):
                                    render_word_card(v)
                                    count += 1
            if count == 0:
                st.info("查無結果。")

    elif menu == "管理區":
        st.title("🛠️ 管理後台")
        pwd = st.text_input("請輸入密碼", type="password")
        if pwd == st.secrets.get("admin_password", "8787"):
            st.json(data)
        elif pwd != "":
            st.error("密碼錯誤")

    elif menu == "學習區":
        ui_quiz_page(data)

    elif menu == "字根區":
        st.title("🗂️ A-Z 字根清單")
        for b in data:
            with st.expander(f"字母區塊: {b['letter']}"):
                for s in b['sub_categories']:
                    st.subheader(f"📂 {s['name']}")
                    for g in s['root_groups']:
                        st.info(f"字根: {'/'.join(g['roots'])} - {g['meaning']}")
                        st.table([{"單字": v['word'], "釋義": v['definition']} for v in g['vocabulary']])
    
    else: # 專業分區
        keyword = menu.replace(" 區", "").strip()
        st.title(f"🔍 {menu}")
        for b in data:
            for s in b.get('sub_categories', []):
                if keyword in s['name']:
                    st.subheader(f"📚 {s['name']}")
                    for g in s['root_groups']:
                        for v in g['vocabulary']:
                            render_word_card(v)

if __name__ == "__main__":
    main()
