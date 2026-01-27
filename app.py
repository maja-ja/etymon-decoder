import streamlit as st
import pandas as pd
import base64
import time
import random
from io import BytesIO
from gtts import gTTS

# ==========================================
# 1. 核心配置與 CSS (完全融合正式版風格)
# ==========================================
st.set_page_config(page_title="Etymon Decoder v2.5", page_icon="🧩", layout="wide")

def inject_custom_css():
    st.markdown("""
        <style>
            html { font-size: 18px; }
            .responsive-word { font-size: 5rem !important; font-weight: 800; color: #1E88E5; text-align: center; }
            .responsive-phonetic { font-size: 1.5rem !important; color: #666; text-align: center; margin-bottom: 20px; }
            .vibe-box {
                background-color: #f0f7ff; padding: 25px; border-left: 10px solid #1E88E5;
                border-radius: 15px; margin: 20px 0; animation: fadeIn 0.8s;
            }
            .breakdown-container {
                font-family: 'Courier New', monospace; font-size: 1.8rem; background: #262730;
                color: white; padding: 15px 30px; border-radius: 50px; display: inline-block; margin: 20px 0;
            }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 工具函式 (音訊與 20 欄讀取)
# ==========================================

def speak(text, key_suffix=""):
    try:
        if not text: return
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        audio_base64 = base64.b64encode(fp.getvalue()).decode()
        unique_id = f"audio_{int(time.time())}_{key_suffix}"
        st.components.v1.html(f'<audio id="{unique_id}" autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio><script>document.getElementById("{unique_id}").play();</script>', height=0)
    except Exception as e: st.error(f"語音錯誤: {e}")

@st.cache_data(ttl=60)
def load_db():
    COL_NAMES = [
        'category', 'roots', 'meaning', 'word', 'breakdown', 
        'definition', 'phonetic', 'example', 'translation', 'native_vibe',
        'synonym_nuance', 'visual_prompt', 'social_status', 'emotional_tone', 'street_usage',
        'collocation', 'etymon_story', 'usage_warning', 'memory_hook', 'audio_tag'
    ]
    # 正式版直接讀取 A:T (20 欄位)
    SHEET_ID = "W1ADPyf5gtGdpIEwkxBEsaJ0bksYldf4AugoXnq6Zvg"
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&range=A:T'
    try:
        df = pd.read_csv(url)
        # 強制對齊 20 欄
        if len(df.columns) < 20:
            for col in COL_NAMES[len(df.columns):]: df[col] = ""
        df.columns = COL_NAMES
        return df.dropna(subset=['word']).fillna("").reset_index(drop=True)
    except: return pd.DataFrame(columns=COL_NAMES)

# ==========================================
# 3. 百科級顯示組件 (融合 native_vibe 解鎖邏輯)
# ==========================================

def show_encyclopedia_card(row):
    # --- 頂部：核心單字區 ---
    st.markdown(f"<div class='responsive-word'>{row['word']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='responsive-phonetic'>/{row['phonetic']}/</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button("🔊 朗讀單字", key=f"btn_{row['word']}"): speak(row['word'], row['word'])
    with col_b:
        st.markdown(f"<div class='breakdown-container'>{row['breakdown']}</div>", unsafe_allow_html=True)

    # --- 中間：定義與字根 ---
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**🎯 定義：** {row['definition']}")
        st.write(f"**📝 例句：** {row['example']}")
        st.caption(f"翻譯：{row['translation']}")
    with c2:
        st.success(f"**💡 字根：** {row['roots']} ({row['meaning']})")
        st.markdown(f"**🪝 記憶點：** {row['memory_hook']}")

    # --- 關鍵：語感解鎖邏輯 (正式版特色) ---
    if row['native_vibe']:
        if not st.session_state.get('vibe_unlocked', False):
            if st.button("🎁 拆開語感驚喜包 (Unlock Native Vibe)", use_container_width=True, type="secondary"):
                st.session_state.vibe_unlocked = True
                st.balloons()
                st.rerun()
        else:
            st.markdown(f"""
                <div class='vibe-box'>
                    <h4 style='color:#1E88E5; margin-top:0;'>🌊 母語人士語感 (Native Vibe)</h4>
                    <p style='font-style: italic; font-size: 1.1rem;'>{row['native_vibe']}</p>
                </div>
            """, unsafe_allow_html=True)

    # --- 底部：百科擴充 (Tabs) ---
    with st.expander("📚 更多深度百科資訊 (字源、社會階層、意象)"):
        tab_a, tab_b, tab_c = st.tabs(["🏛️ 文化與字源", "👔 社會意象", "😎 街頭實戰"])
        with tab_a:
            st.write(f"**📜 字源故事：** {row['etymon_story']}")
            st.write(f"**⚖️ 同義詞辨析：** {row['synonym_nuance']}")
        with tab_b:
            st.write(f"**🎨 視覺意象：** {row['visual_prompt']}")
            st.write(f"**👔 社會地位感：** {row['social_status']}")
            st.write(f"**🌡️ 情緒色調：** {row['emotional_tone']}")
        with tab_c:
            st.write(f"**🏙️ 街頭用法：** {row['street_usage']}")
            st.write(f"**🔗 常用搭配：** {row['collocation']}")
            if row['usage_warning']:
                st.error(f"⚠️ 警告：{row['usage_warning']}")

# ==========================================
# 4. 頁面整合
# ==========================================

def page_learn_search(df):
    st.title("📖 學習與搜尋")
    tab_card, tab_list = st.tabs(["隨機單字卡", "資料庫列表"])
    
    with tab_card:
        # 分類過濾
        cats = ["全部"] + sorted(df['category'].unique().tolist())
        sel_cat = st.selectbox("選擇分類", cats, key="cat_sel")
        f_df = df if sel_cat == "全部" else df[df['category'] == sel_cat]

        if not f_df.empty:
            if 'curr_w' not in st.session_state:
                st.session_state.curr_w = f_df.sample(1).iloc[0].to_dict()
                st.session_state.vibe_unlocked = False

            if st.button("下一個單字 (Next Word) ➔", use_container_width=True, type="primary"):
                st.session_state.curr_w = f_df.sample(1).iloc[0].to_dict()
                st.session_state.vibe_unlocked = False
                st.rerun()

            show_encyclopedia_card(st.session_state.curr_w)

    with tab_list:
        search = st.text_input("🔍 搜尋單字或中文...", placeholder="輸入關鍵字...")
        if search:
            mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
            st.dataframe(df[mask][['word', 'definition', 'roots', 'category']], use_container_width=True)
        else:
            st.dataframe(df[['word', 'definition', 'roots', 'category']].head(50), use_container_width=True)

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
