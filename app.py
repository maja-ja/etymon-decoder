import streamlit as st
import pandas as pd
import base64
import time
import random
from io import BytesIO
from gtts import gTTS

# ==========================================
# 1. 核心配置與 CSS (Config & CSS)
# ==========================================
st.set_page_config(
    page_title="Etymon Decoder",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Sheet 設定
SHEET_ID = '1W1ADPyf5gtGdpIEwkxBEsaJ0bksYldf4AugoXnq6Zvg'

def inject_custom_css():
    """注入全域自適應 CSS"""
    st.markdown("""
        <style>
            html { font-size: 18px; } 
            @media (max-width: 600px) {
                .responsive-word { font-size: 12vw !important; }
                .responsive-text { font-size: 4.5vw !important; }
            }
            .vibe-box {
                background-color: #f0f7ff; 
                padding: 20px; 
                border-left: 5px solid #1E88E5; 
                border-radius: 10px; 
                margin: 15px 0;
            }
            .stats-box {
                text-align: center; 
                padding: 15px; 
                background-color: #f8f9fa; 
                border-radius: 12px;
                border: 1px solid #dee2e6;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 工具函式 (Utils)
# ==========================================

def speak(text, key_suffix=""):
    """瀏覽器端語音播放"""
    try:
        if not text or pd.isna(text): return
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        audio_base64 = base64.b64encode(fp.getvalue()).decode()
        unique_id = f"audio_{int(time.time())}_{key_suffix}"
        audio_html = f"""
            <audio id="{unique_id}" autoplay="true" style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>document.getElementById("{unique_id}").play();</script>
        """
        st.components.v1.html(audio_html, height=0)
    except Exception as e:
        st.error(f"語音生成失敗: {e}")

@st.cache_data(ttl=60)
def load_db():
    """載入 20 欄位百科級資料庫"""
    COL_NAMES = [
        'category', 'roots', 'meaning', 'word', 'breakdown', 
        'definition', 'phonetic', 'example', 'translation', 'native_vibe',
        'synonym_nuance', 'visual_prompt', 'social_status', 'emotional_tone', 'street_usage',
        'collocation', 'etymon_story', 'usage_warning', 'memory_hook', 'audio_tag'
    ]
    range_str = "A:T"
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&range={range_str}'
    
    try:
        df = pd.read_csv(url)
        if len(df.columns) >= len(COL_NAMES):
            df.columns = COL_NAMES[:len(df.columns)]
        else:
            for i, col in enumerate(COL_NAMES):
                if i >= len(df.columns): df[col] = ""
            df.columns = COL_NAMES
        df = df.dropna(subset=['word']).fillna("")
        df['word'] = df['word'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return pd.DataFrame(columns=COL_NAMES)

# ==========================================
# 3. 顯示邏輯 (Display UI)
# ==========================================

def show_word_encyclopedia(row):
    """20 欄位百科風美化顯示"""
    # 單字標題與發音按鈕
    c_title, c_audio = st.columns([4, 1])
    with c_title:
        st.markdown(f"<h1 class='responsive-word' style='color: #1E88E5;'>{row['word']}</h1>", unsafe_allow_html=True)
    with c_audio:
        if st.button("🔊 朗讀", key=f"sp_{row['word']}"):
            speak(row['word'], key_suffix=row['word'])

    # 基礎資訊
    st.markdown(f"**🔈 音標：** `{row['phonetic']}` | **🏗️ 結構：** `{row['breakdown']}`")

    # 靈魂語感 (Native Vibe)
    st.markdown(f"""
    <div class="vibe-box">
        <h4 style="margin-top:0; color: #1565C0;">🌊 核心語感 (Native Vibe)</h4>
        <p class="responsive-text" style="font-style: italic; font-size: 1.2rem;">{row['native_vibe']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 定義與例句
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**🎯 中文定義**\n\n{row['definition']}")
    with c2:
        st.success(f"**💡 字根 ({row['roots']})**\n\n{row['meaning']}")

    st.markdown(f"**📝 實戰例句**\n> {row['example']}\n\n*{row['translation']}*")

    # 深度與街頭 (Expanders)
    with st.expander("✨ 深度意象與社會洞察"):
        cx, cy = st.columns(2)
        with cx:
            st.markdown(f"**🎨 視覺意象:** \n{row['visual_prompt']}")
            st.markdown(f"**🌡️ 情緒色調:** {row['emotional_tone']}")
        with cy:
            st.markdown(f"**👔 社會定位:** {row['social_status']}")
            st.markdown(f"**⚖️ 同義詞辨析:** \n{row['synonym_nuance']}")

    with st.expander("🏙️ 街頭用法與地雷警告"):
        st.warning(f"**😎 街頭/非正式用法:** \n\n{row['street_usage']}")
        st.write(f"**🔗 常用搭配:** {row['collocation']}")
        if row['usage_warning']:
            st.error(f"**⚠️ 使用禁忌:** {row['usage_warning']}")

    st.markdown("---")
    st.caption(f"📜 字源故事：{row['etymon_story']}")
    st.markdown(f"🪝 **記憶鉤子：** <span style='color: #D81B60; font-weight: bold;'>{row['memory_hook']}</span>", unsafe_allow_html=True)

# ==========================================
# 4. 頁面邏輯 (Pages)
# ==========================================

def page_home(df):
    st.markdown("<h1 style='text-align: center;'>Etymon Decoder</h1>", unsafe_allow_html=True)
    st.write("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("總單字量", len(df))
    c2.metric("分類主題", df['category'].nunique())
    c3.metric("獨特字根", df['roots'].nunique())
    st.info("👈 請從左側選單選擇「學習與搜尋」開始解碼。")

def page_learn_search(df):
    st.title("📖 學習與搜尋")
    
    # 搜尋功能
    search_mode = st.radio("模式", ["快速查詢", "隨機探索"], horizontal=True)
    
    if search_mode == "快速查詢":
        search_word = st.selectbox("請選擇或輸入單字", [""] + sorted(df['word'].tolist()))
        if search_word:
            row = df[df['word'] == search_word].iloc[0]
            show_word_encyclopedia(row)
    else:
        if st.button("🎲 隨機來一個單字"):
            st.session_state.random_word = df.sample(1).iloc[0].to_dict()
        
        if 'random_word' in st.session_state:
            show_word_encyclopedia(st.session_state.random_word)

def page_quiz(df):
    st.title("🧠 字根挑戰賽")
    cat = st.selectbox("測驗範圍", df['category'].unique())
    pool = df[df['category'] == cat]
    
    if st.button("開始測驗 / 下一題"):
        st.session_state.q = pool.sample(1).iloc[0].to_dict()
        st.session_state.show_ans = False

    if 'q' in st.session_state:
        st.subheader("請問這個定義對應哪個單字？")
        st.info(st.session_state.q['definition'])
        st.write(f"提示 (字根): {st.session_state.q['roots']}")
        
        if st.button("看答案"):
            st.session_state.show_ans = True
        
        if st.session_state.show_ans:
            st.success(f"答案是：{st.session_state.q['word']}")
            speak(st.session_state.q['word'], "quiz")
            st.write(f"結構：{st.session_state.q['breakdown']}")

# ==========================================
# 5. 主程式入口
# ==========================================
def main():
    inject_custom_css()
    df = load_db()
    if df.empty: return

    page = st.sidebar.radio("導航", ["首頁", "學習與搜尋", "測驗模式"])
    
    if page == "首頁": page_home(df)
    elif page == "學習與搜尋": page_learn_search(df)
    elif page == "測驗模式": page_quiz(df)

if __name__ == "__main__":
    main()
