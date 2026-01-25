import streamlit as st
import json
import random
import pandas as pd
import base64
import time
from io import BytesIO
from gtts import gTTS
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 核心功能：發音 (僅供學習區使用)
# ==========================================
def speak(text):
    if not text: return
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode()
        comp_id = int(time.time() * 1000)
        audio_html = f"""
            <audio autoplay id="aud_{comp_id}">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>document.getElementById("aud_{comp_id}").play();</script>
        """
        st.components.v1.html(audio_html, height=0)
    except Exception:
        pass

# ==========================================
# 2. 資料載入 (針對 A-Z 區塊邏輯優化)
# ==========================================
@st.cache_data(ttl=600)
def load_db():
    import string
    # 請確保 SHEET_ID 是你最新的那一個
    SHEET_ID = '1Gs0FX7c8bUQTnSytX1EqjMLATeVc30GmdjSOYW_sYsQ'
    GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx:out:csv'
    
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
# 3. UI 修飾組件
# ==========================================

def render_word_card(v, theme_color="#1E88E5"):
    """純文字美化單字卡"""
    with st.container(border=True):
        st.markdown(f"### <span style='color:{theme_color}'>{v['word']}</span>", unsafe_allow_html=True)
        if v.get('phonetic') and str(v['phonetic']) != 'nan' and v['phonetic'] != "":
            st.caption(f"/{v['phonetic'].strip('/')}/")
        
        st.write(f"**構成：** `{v['breakdown']}`")
        st.write(f"**定義：** {v['definition']}")
        
        if v.get('example') and str(v['example']) != 'nan' and v['example'] != "":
            with st.expander("查看例句與翻譯"):
                st.write(v['example'])
                if v.get('translation') and str(v['translation']) != 'nan':
                    st.caption(f"({v['translation']})")

def ui_quiz_page(data):
    """美化測驗區：保留語音按鈕"""
    st.title("🎯 學習區 (Flashcards)")
    pool = []
    for block in data:
        for sub in block.get('sub_categories', []):
            for group in sub.get('root_groups', []):
                for v in group.get('vocabulary', []):
                    item = v.copy()
                    item['cat'] = sub['name']
                    pool.append(item)
    
    if not pool:
        st.warning("目前沒有單字可供練習。")
        return

    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False

    q = st.session_state.flash_q
    
    # 卡片外觀修飾
    st.markdown(f"""
        <div style="text-align: center; padding: 40px; border: 2px solid #1E88E5; 
                    border-radius: 20px; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <p style="color: #666; font-weight: bold;">[ 分類：{q['cat']} ]</p>
            <h1 style="font-size: 4.5em; color: #1E88E5; margin: 10px 0;">{q['word']}</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👀 顯示答案", use_container_width=True):
            st.session_state.flipped = True
    with c2:
        if st.button("🔊 播放發音", use_container_width=True):
            speak(q['word'])
    with c3:
        if st.button("➡️ 下一個", use_container_width=True):
            st.session_state.flash_q = random.choice(pool)
            st.session_state.flipped = False
            st.rerun()

    if st.session_state.get('flipped'):
        st.markdown(f"""
            <div style="background: #f0f7ff; padding: 25px; border-radius: 15px; border-left: 10px solid #1E88E5; margin-top: 20px;">
                <h3 style="margin: 0; color: #1E88E5;">構成：<span style="color:#d32f2f;">{q['breakdown']}</span></h3>
                <p style="font-size: 1.4em; margin-top: 10px;"><b>定義：</b>{q['definition']}</p>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程序入口
# ==========================================

def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    data = load_db()
    
    # 計算單字總數
    total_words = sum(len(g['vocabulary']) for b in data for s in b['sub_categories'] for g in s['root_groups'])

    # 側邊欄美化
    st.sidebar.title("🧬 Etymon Decoder")
    menu = st.sidebar.radio("導航選單", ["搜尋與瀏覽", "字根區", "學習區", "醫學區", "法律區", "管理區"])
    
    # 資料庫總量儀表板 (修正 HTML 顯示問題)
    st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: #f0f2f6; border-radius: 12px; margin-top: 20px;">
            <p style="margin: 0; font-size: 0.9em; color: #666;">資料庫總計</p>
            <p style="margin: 0; font-size: 2.2em; font-weight: bold; color: #1E88E5;">{total_words}</p>
            <p style="margin: 0; font-size: 0.8em; color: #666;">Words</p>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🔄 刷新雲端資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # 頁面跳轉邏輯
    if menu == "搜尋與瀏覽":
        st.title("🔍 全域單字搜尋")
        query = st.text_input("輸入關鍵字 (單字/中文/字根)...").strip().lower()
        if query:
            count = 0
            for b in data:
                for s in b['sub_categories']:
                    for g in s['root_groups']:
                        for v in g['vocabulary']:
                            if query in v['word'].lower() or query in v['definition'].lower():
                                with st.expander(f"📖 {v['word']} ({s['name']})"):
                                    render_word_card(v)
                                    count += 1
            if count == 0: st.info("查無結果。")

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
    
    elif menu == "管理區":
        st.title("🛠️ 管理員模式")
        pwd = st.text_input("輸入密碼", type="password")
        if pwd == st.secrets.get("admin_password", "8787"):
            st.json(data)

    else: # 專業分區 (醫學/法律等)
        keyword = menu.replace("區", "").strip()
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
