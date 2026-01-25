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
# 1. 核心發音功能 (僅在學習區使用，避免卡頓)
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
            <audio autoplay id="aud_{comp_id}"><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>
            <script>document.getElementById("aud_{comp_id}").play();</script>
        """
        st.components.v1.html(audio_html, height=0)
    except Exception:
        pass

# ==========================================
# 2. 資料載入 (優化讀取範圍)
# ==========================================
@st.cache_data(ttl=600)
def load_db():
    SHEET_ID = '1W1ADPyf5gtGdpIEwkxBEsaJ0bksYldf4AugoXnq6Zvg'
    GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
    BLOCKS = ["A:I", "J:R", "S:AA", "AB:AJ", "AK:AS"]
    all_dfs = []
    for rng in BLOCKS:
        try:
            url = f"{GSHEET_URL}&range={rng}"
            df_part = pd.read_csv(url).dropna(how='all').iloc[:, :9]
            df_part.columns = ['category', 'roots', 'meaning', 'word', 'breakdown', 'definition', 'phonetic', 'example', 'translation']
            all_dfs.append(df_part)
        except: continue
    if not all_dfs: return []
    df = pd.concat(all_dfs, ignore_index=True).dropna(subset=['category'])
    
    structured_data = []
    for cat_name, cat_group in df.groupby('category'):
        root_groups = []
        for (roots, meaning), group_df in cat_group.groupby(['roots', 'meaning']):
            vocabulary = []
            for _, row in group_df.iterrows():
                if pd.isna(row['word']): continue
                vocabulary.append({
                    "word": str(row['word']), "breakdown": str(row['breakdown']),
                    "definition": str(row['definition']), "phonetic": str(row['phonetic']),
                    "example": str(row['example']), "translation": str(row['translation'])
                })
            root_groups.append({"roots": str(roots).split('/'), "meaning": str(meaning), "vocabulary": vocabulary})
        structured_data.append({"category": str(cat_name), "root_groups": root_groups})
    return structured_data

# ==========================================
# 3. 修飾後的 UI 組件
# ==========================================

def ui_domain_page(domain_data, title, theme_color):
    """修飾後的分區顯示：改用面板與表格，極速載入"""
    st.title(title)
    if not domain_data:
        st.info("目前尚無資料")
        return

    for cat in domain_data:
        st.subheader(f"📂 {cat['category']}")
        for group in cat['root_groups']:
            # 使用 Expander 減少視覺負擔
            with st.expander(f"✨ 字根：{'/'.join(group['roots'])} ({group['meaning']})"):
                # 將單字轉為 DataFrame 顯示，這是最不會讓右上角出現 Stop 的做法
                display_df = pd.DataFrame(group['vocabulary'])
                if not display_df.empty:
                    # 只選取重要的欄位
                    st.table(display_df[['word', 'breakdown', 'definition', 'translation']])

def ui_quiz_page(data):
    """保留並美化學習區的單字卡"""
    st.title("🎴 學習區 (Flashcards)")
    pool = [{**v, "cat": c['category']} for c in data for g in c['root_groups'] for v in g['vocabulary']]
    
    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False

    q = st.session_state.flash_q

    # 美化卡片正面
    st.markdown(f"""
        <div style="text-align: center; padding: 50px; border: 2px solid { '#1E88E5' if not '法律' in q['cat'] else '#FFD700' }; 
                    border-radius: 20px; background: white; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <p style="color: gray;">[ {q['cat']} ]</p>
            <h1 style="font-size: 5em; margin: 0; color: #1E88E5;">{q['word']}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👀 顯示答案", use_container_width=True): st.session_state.flipped = True
    with c2:
        if st.button("🔊 播放", use_container_width=True): speak(q['word'])
    with c3:
        if st.button("➡️ 下一題", use_container_width=True):
            st.session_state.flash_q = random.choice(pool)
            st.session_state.flipped = False
            st.rerun()

    if st.session_state.flipped:
        st.markdown(f"""
            <div style="background: #f0f7ff; padding: 25px; border-radius: 15px; border-left: 10px solid #1E88E5; margin-top: 20px;">
                <h3 style="margin-top:0;">構成：<span style="color:red;">{q['breakdown']}</span></h3>
                <p style="font-size: 1.5em;"><b>釋義：</b>{q['definition']}</p>
                <p style="font-size: 1.1em; color: #555;"><i>{q['example']}</i></p>
                <p style="font-size: 0.9em; color: #888;">({q['translation']})</p>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程式導航
# ==========================================
def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    data = load_db()
    
    # 側邊欄美化
    st.sidebar.title("🧬 Etymon Decoder")
    menu = st.sidebar.radio("導航選單", ["字根搜尋", "學習區", "高中核心", "醫學專業", "法律術語", "人工智慧", "心理社會", "生物自然", "管理區"])
    
    total_words = sum(len(g['vocabulary']) for c in data for g in c['root_groups'])
    st.sidebar.markdown(f"""---
    <div style="text-align:center;">資料庫總量<br><b style="font-size:2em;">{total_words}</b> Words</div>""", unsafe_allow_html=True)

    if menu == "學習區":
        ui_quiz_page(data)
    
    elif menu == "字根搜尋":
        st.title("🔍 全域搜尋")
        query = st.text_input("輸入單字或字根關鍵字...")
        if query:
            for c in data:
                for g in c['root_groups']:
                    matched = [v for v in g['vocabulary'] if query.lower() in v['word'].lower()]
                    if matched:
                        with st.expander(f"📖 {g['roots']} - {g['meaning']} (來自 {c['category']})"):
                            st.table(pd.DataFrame(matched)[['word', 'definition', 'translation']])

    elif menu == "管理區":
        st.title("🛡️ 管理員控制台")
        pwd = st.text_input("密碼", type="password")
        if pwd == st.secrets.get("admin_password", "8787"):
            st.json(data)

    else: # 專業分區邏輯
        mapping = {
            "高中核心": "高中", "醫學專業": "醫學", "法律術語": "法律",
            "人工智慧": "AI", "心理社會": "心理", "生物自然": "生物"
        }
        keyword = mapping.get(menu, menu)
        filtered = [c for c in data if keyword in c['category']]
        ui_domain_page(filtered, f"{menu}分區", "#1E88E5")

if __name__ == "__main__":
    main()
