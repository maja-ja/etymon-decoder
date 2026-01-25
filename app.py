import streamlit as st
import json
import os
import random
import pandas as pd
import base64
from io import BytesIO
from gtts import gTTS
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 樣式與語音核心功能
# ==========================================

def inject_custom_css():
    """注入 CSS 確保手機與電腦文字比例正確"""
    st.markdown("""
        <style>
            /* 基礎文字縮放 */
            html { font-size: 16px; }
            
            /* 自適應字體類別 */
            .responsive-word { font-weight: bold; line-height: 1.2; }
            .responsive-breakdown { font-family: 'Courier New', monospace; font-weight: bold; background: #444; color: #FFD700; padding: 4px 12px; border-radius: 8px; border: 1px solid #FFD700; display: inline-block; }
            
            /* 手機端優化 (小於 600px) */
            @media (max-width: 600px) {
                .responsive-word { font-size: 10vw !important; }
                .responsive-breakdown { font-size: 5vw !important; }
                .responsive-def { font-size: 4.5vw !important; }
                .quiz-card-word { font-size: 15vw !important; }
                .stButton button { width: 100%; } /* 手機按鈕撐滿 */
            }
            
            /* 電腦端優化 (大於 600px) */
            @media (min-width: 601px) {
                .responsive-word { font-size: 2.5rem !important; }
                .responsive-breakdown { font-size: 1.4rem !important; }
                .responsive-def { font-size: 1.2rem !important; }
                .quiz-card-word { font-size: 5rem !important; }
            }

            /* 卡片樣式 */
            .quiz-container {
                text-align: center; 
                padding: 5vh 2vw; 
                border: 2px solid #eee; 
                border-radius: 25px; 
                background: #fdfdfd; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            }
        </style>
    """, unsafe_allow_html=True)

def speak(text):
    """改良版語音：直接注入 HTML5 音訊標籤"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode()
        
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        # 放在一個微小的 placeholder 中
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"語音錯誤: {e}")

# ==========================================
# 2. 資料處理邏輯
# ==========================================

SHEET_ID = '1W1ADPyf5gtGdpIEwkxBEsaJ0bksYldf4AugoXnq6Zvg'
GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
FEEDBACK_URL = st.secrets.get("feedback_sheet_url")

@st.cache_data(ttl=600)
def load_db():
    BLOCKS = ["A:I", "J:R", "S:AA", "AB:AJ", "AK:AS"]
    all_dfs = []
    for rng in BLOCKS:
        try:
            url = f"{GSHEET_URL}&range={rng}"
            df_part = pd.read_csv(url)
            df_part = df_part.dropna(how='all')
            if not df_part.empty:
                df_part = df_part.iloc[:, :9]
                df_part.columns = ['category', 'roots', 'meaning', 'word', 'breakdown', 'definition', 'phonetic', 'example', 'translation']
                all_dfs.append(df_part)
        except: continue

    if not all_dfs: return []
    df = pd.concat(all_dfs, ignore_index=True).dropna(subset=['category'])
    
    structured_data = []
    for cat_name, cat_group in df.groupby('category'):
        root_groups = []
        for (roots, meaning), group_df in cat_group.groupby(['roots', 'meaning']):
            vocabulary = [{
                "word": str(row['word']),
                "breakdown": str(row['breakdown']),
                "definition": str(row['definition']),
                "phonetic": str(row['phonetic']) if pd.notna(row['phonetic']) else "",
                "example": str(row['example']) if pd.notna(row['example']) else "",
                "translation": str(row['translation']) if pd.notna(row['translation']) else ""
            } for _, row in group_df.iterrows()]
            root_groups.append({"roots": [r.strip() for r in str(roots).split('/')], "meaning": str(meaning), "vocabulary": vocabulary})
        structured_data.append({"category": str(cat_name), "root_groups": root_groups})
    return structured_data

def save_feedback_to_gsheet(word, feedback_type, comment):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=FEEDBACK_URL, ttl=0)
        new_row = pd.DataFrame([{
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "word": word, "type": feedback_type, "comment": comment, "status": "pending"
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(spreadsheet=FEEDBACK_URL, data=updated_df)
        st.success(f"✅ 回報已同步！")
    except Exception as e:
        st.error(f"❌ 同步失敗: {e}")

# ==========================================
# 3. UI 組件
# ==========================================

def ui_feedback_component(word):
    with st.popover("⚠️ 錯誤回報"):
        f_type = st.selectbox("錯誤類型", ["發音錯誤", "拆解有誤", "中文釋義錯誤", "其他"], key=f"err_t_{word}")
        f_comment = st.text_area("說明", key=f"err_n_{word}")
        if st.button("提交", key=f"err_b_{word}"):
            if f_comment.strip():
                save_feedback_to_gsheet(word, f_type, f_comment)
            else: st.warning("請填寫內容")

def ui_domain_page(domain_data, title, theme_color, bg_color):
    st.title(title)
    if not domain_data:
        st.info("尚無資料"); return

    root_map = {}
    for cat in domain_data:
        for group in cat.get('root_groups', []):
            label = f"{'/'.join(group['roots'])} ({group['meaning']})"
            root_map[label] = group
    
    selected_label = st.selectbox("選擇字根", sorted(root_map.keys()), key=title)
    
    if selected_label:
        for v in root_map[selected_label].get('vocabulary', []):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    color = "#FFD700" if "法律" in title else theme_color
                    st.markdown(f'<div class="responsive-word" style="color:{color};">{v["word"]}</div>', unsafe_allow_html=True)
                with col2:
                    if st.button("🔊 播放", key=f"play_{v['word']}_{title}"): speak(v['word'])
                    ui_feedback_component(v['word'])
                
                st.markdown(f"""
                    <div style="margin-bottom: 20px;">
                        <div class="responsive-breakdown">{v['breakdown']}</div>
                        <div class="responsive-def" style="margin-top:10px;"><b>釋義：</b>{v['definition']}</div>
                    </div>
                    <hr style="opacity:0.2;">
                """, unsafe_allow_html=True)

def ui_quiz_page(data):
    st.title("學習區 (Flashcards)")
    pool = [{**v, "cat": c['category']} for c in data for g in c['root_groups'] for v in g['vocabulary']]
    
    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False

    q = st.session_state.flash_q

    # 單字卡片
    st.markdown(f"""
        <div class="quiz-container">
            <p style="color:#888;">[ {q['cat']} ]</p>
            <div class="quiz-card-word" style="color:#1E88E5;">{q['word']}</div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👁️ 查看答案", use_container_width=True): st.session_state.flipped = True
    with c2:
        if st.button("🔊 播放", use_container_width=True): speak(q['word'])
    with c3:
        if st.button("➡️ 下一題", use_container_width=True):
            st.session_state.flash_q = random.choice(pool)
            st.session_state.flipped = False
            st.rerun()

    if st.session_state.flipped:
        st.markdown(f"""
            <div style="background:#f0f8ff; padding:20px; border-radius:15px; border-left:8px solid #1E88E5;">
                <div class="responsive-breakdown">{q['breakdown']}</div>
                <div class="responsive-def" style="margin-top:10px; font-size:1.5rem;">{q['definition']}</div>
                <div style="color:#666; font-style:italic; margin-top:10px;">{q['example']}</div>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程式
# ==========================================

def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    inject_custom_css()
    data = load_db()
    
    menu = st.sidebar.radio("導航", ["字根瀏覽", "學習區", "國小區", "國中區", "高中區", "醫學區", "法律區", "AI區", "管理區"])
    
    if st.sidebar.button("🔄 強制刷新數據"):
        st.cache_data.clear()
        st.rerun()

    if menu == "字根瀏覽":
        ui_domain_page(data, "所有字根", "#1E88E5", "#FFF")
    elif menu == "學習區":
        ui_quiz_page(data)
    elif menu == "法律區":
        law = [c for c in data if "法律" in str(c.get('category'))]
        ui_domain_page(law, "法律專業字根", "#FFD700", "#1A1A1A")
    # ... 其餘區塊以此類推呼叫 ui_domain_page ...

if __name__ == "__main__":
    main()
