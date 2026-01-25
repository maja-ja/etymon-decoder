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
# 1. 核心發音功能 (僅在點擊時觸發，避免背景 Stop)
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
        # 加上 height=0 避免影響布局
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
# 2. 資料載入 (優化讀取速度)
# ==========================================
@st.cache_data(ttl=600)
def load_db():
    # 請確保 SHEET_ID 是正確的
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

def ui_quiz_page(data):
    """學習區：精美卡片 + 喇叭按鈕"""
    st.title("學習區 (Flashcards)")
    pool = [{**v, "cat": c['category']} for c in data for g in c['root_groups'] for v in g['vocabulary']]
    
    if not pool:
        st.warning("資料庫目前沒有單字")
        return

    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False

    q = st.session_state.flash_q

    # 卡片 UI
    st.markdown(f"""
        <div style="text-align: center; padding: 40px; border: 2px solid #1E88E5; 
                    border-radius: 20px; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <p style="color: #1E88E5; font-weight: bold; margin-bottom: 10px;">📍 {q['cat']}</p>
            <h1 style="font-size: 4.5em; margin: 0; color: #333;">{q['word']}</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("顯示答案", use_container_width=True): st.session_state.flipped = True
    with c2:
        if st.button("播放發音", use_container_width=True): speak(q['word'])
    with c3:
        if st.button("➡️ 下一題", use_container_width=True):
            st.session_state.flash_q = random.choice(pool)
            st.session_state.flipped = False
            st.rerun()

    if st.session_state.flipped:
        st.markdown(f"""
            <div style="background: #f0f7ff; padding: 20px; border-radius: 15px; border-left: 8px solid #1E88E5; margin-top: 15px;">
                <h3 style="margin: 0; color: #1E88E5;">構成：<span style="color:#d32f2f;">{q['breakdown']}</span></h3>
                <p style="font-size: 1.4em; margin-top: 10px;"><b>釋義：</b>{q['definition']}</p>
                <hr style="border: 0.5px solid #d0e3ff;">
                <p style="font-style: italic; color: #555;">{q['example']}</p>
                <p style="font-size: 0.9em; color: #888;">({q['translation']})</p>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程式入口
# ==========================================
def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    data = load_db()
    
    # 側邊欄導航
    st.sidebar.title("Etymon Decoder")
    menu = st.sidebar.radio("導航", ["學習區", "字根區", "醫學區", "法律區", "高中核心", "管理區"])
    
    # 計算單字總數
    total_words = sum(len(g['vocabulary']) for c in data for g in c['root_groups'])

    # 修正您的 HTML 顯示問題（關鍵在於 unsafe_allow_html=True）
    st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: #f0f2f6; border-radius: 12px; margin-top: 20px;">
            <p style="margin: 0; font-size: 0.9em; color: #666;">資料庫總計</p>
            <p style="margin: 0; font-size: 2.2em; font-weight: bold; color: #1E88E5;">{total_words}</p>
            <p style="margin: 0; font-size: 0.8em; color: #666;">Words</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("刷新資料"):
        st.cache_data.clear()
        st.rerun()

    # 頁面分流
    if menu == "學習區":
        ui_quiz_page(data)
    
    elif menu == "字根區":
        st.title("字根總覽與搜尋")
        q = st.text_input("輸入字根或單字搜尋...")
        for c in data:
            with st.expander(f"📂 {c['category']}"):
                for g in c['root_groups']:
                    st.info(f"字根：{'/'.join(g['roots'])} ({g['meaning']})")
                    df = pd.DataFrame(g['vocabulary'])
                    if q: # 搜尋過濾
                        df = df[df['word'].str.contains(q, case=False) | df['definition'].str.contains(q, case=False)]
                    if not df.empty:
                        st.table(df[['word', 'breakdown', 'definition']])

    elif menu == "管理區":
        st.title("管理後台")
        pwd = st.text_input("管理員密碼", type="password")
        if pwd == st.secrets.get("admin_password", "8787"):
            st.json(data)
        elif pwd: st.error("密碼錯誤")

    else: # 專業分區
        keyword = menu.replace("區", "")
        filtered = [c for c in data if keyword in c['category']]
        st.title(f"{menu}")
        for c in filtered:
            for g in c['root_groups']:
                with st.expander(f"✨ {'/'.join(g['roots'])} ({g['meaning']})"):
                    st.table(pd.DataFrame(g['vocabulary'])[['word', 'breakdown', 'definition']])

if __name__ == "__main__":
    main()
