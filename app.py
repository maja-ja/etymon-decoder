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
# 新增：全域自適應 CSS (只新增不刪減功能)
# ==========================================
def inject_custom_css():
    st.markdown("""
        <style>
            /* 基礎縮放邏輯 */
            html { font-size: 16px; }
            
            /* 手機端 (寬度小於 600px) 文字與排版優化 */
            @media (max-width: 600px) {
                .responsive-title { font-size: 8vw !important; }
                .responsive-word { font-size: 10vw !important; }
                .responsive-breakdown { font-size: 5vw !important; padding: 3px 8px !important; }
                .responsive-text { font-size: 4.5vw !important; }
                .stButton button { width: 100%; margin-bottom: 5px; } /* 手機按鈕撐滿 */
            }
            
            /* 電腦端基礎尺寸 */
            @media (min-width: 601px) {
                .responsive-title { font-size: 2.5rem !important; }
                .responsive-word { font-size: 2.2rem !important; }
                .responsive-breakdown { font-size: 1.6rem !important; }
                .responsive-text { font-size: 1.3rem !important; }
            }

            /* 統一拆解框樣式 */
            .breakdown-container {
                font-family: 'Courier New', monospace;
                font-weight: bold;
                background: #888;
                color: #FFD700;
                padding: 4px 12px;
                border-radius: 8px;
                border: 1px solid #FFD700;
                text-shadow: 1px 1px 2px black;
                display: inline-block;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 修正語音發音 (改良為 HTML5 標籤)
# ==========================================
def speak(text):
    """改良版：使用更穩定的 HTML5 播放屬性"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode()
        
        audio_html = f"""
            <audio autoplay="true">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"語音錯誤: {e}")

# ==========================================
# 1. 核心配置與雲端同步 (保留原代碼)
# ==========================================
SHEET_ID = '1W1ADPyf5gtGdpIEwkxBEsaJ0bksYldf4AugoXnq6Zvg'
GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
PENDING_FILE = 'pending_data.json'
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
            vocabulary = []
            for _, row in group_df.iterrows():
                vocabulary.append({
                    "word": str(row['word']),
                    "breakdown": str(row['breakdown']),
                    "definition": str(row['definition']),
                    "phonetic": str(row['phonetic']) if pd.notna(row['phonetic']) else "",
                    "example": str(row['example']) if pd.notna(row['example']) else "",
                    "translation": str(row['translation']) if pd.notna(row['translation']) else ""
                })
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
        st.success(f"✅ 單字「{word}」的回報已同步至雲端！")
    except Exception as e:
        st.error(f"❌ 雲端同步失敗。")
        st.caption(f"錯誤詳情: {e}")

def get_stats(data):
    if not data: return 0, 0
    total_words = sum(len(g.get('vocabulary', [])) for cat in data for g in cat.get('root_groups', []))
    return len(data), total_words

# ==========================================
# 2. 通用與專業區域組件 (調整為自適應樣式)
# ==========================================
def ui_domain_page(domain_data, title, theme_color, bg_color):
    st.markdown(f'<div class="responsive-title" style="font-weight:bold; margin-bottom:10px;">{title}</div>', unsafe_allow_html=True)
    if not domain_data:
        st.info("目前資料庫中尚未建立相關分類。")
        return

    root_map = {}
    for cat in domain_data:
        for group in cat.get('root_groups', []):
            label = f"{'/'.join(group['roots'])} ({group['meaning']})"
            if label not in root_map: root_map[label] = group
    
    selected_label = st.selectbox("選擇要複習的字根", sorted(root_map.keys()), key=title)
    
    if selected_label:
        group = root_map[selected_label]
        for v in group.get('vocabulary', []):
            with st.container():
                col_word, col_play, col_report = st.columns([3, 1, 1])
                with col_word:
                    display_color = "#FFD700" if "法律" in title else theme_color
                    st.markdown(f'<div class="responsive-word" style="font-weight: bold; color: {display_color};">{v["word"]}</div>', unsafe_allow_html=True)
                with col_play:
                    if st.button("播放", key=f"v_{v['word']}_{title}"): speak(v['word'])
                with col_report:
                    ui_feedback_component(v['word'])
                
                st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <span style="color: #888;">構造拆解：</span><br>
                        <span class="breakdown-container responsive-breakdown">{v['breakdown']}</span>
                        <div class="responsive-text" style="color: #DDD; margin-top: 10px;"><b>中文定義：</b> {v['definition']}</div>
                    </div>
                    <hr style="border-color: #444;">
                """, unsafe_allow_html=True)

def ui_feedback_component(word):
    with st.popover("錯誤回報"):
        st.write(f"回報單字：**{word}**")
        f_type = st.selectbox("錯誤類型", ["發音錯誤", "拆解有誤", "中文釋義錯誤", "分類錯誤", "其他"], key=f"err_type_{word}")
        f_comment = st.text_area("詳細說明", placeholder="請描述正確的資訊...", key=f"err_note_{word}")
        if st.button("提交回報", key=f"err_btn_{word}"):
            if f_comment.strip() == "": st.error("請填寫說明內容")
            else:
                save_feedback_to_gsheet(word, f_type, f_comment)
                st.success("感謝回報！")

def ui_quiz_page(data):
    st.markdown('<div class="responsive-title" style="font-weight:bold;">學習區 (Flashcards)</div>', unsafe_allow_html=True)
    cat_options_map = {"全部練習": "全部練習"}
    cat_options_list = ["全部練習"]
    for c in data:
        w_count = sum(len(g['vocabulary']) for g in c['root_groups'])
        display_name = f"{c['category']} ({w_count} 字)"
        cat_options_list.append(display_name)
        cat_options_map[display_name] = c['category']

    selected_raw = st.selectbox("選擇練習範圍", sorted(cat_options_list))
    selected_cat = cat_options_map[selected_raw]

    if st.session_state.get('last_quiz_cat') != selected_cat:
        st.session_state.last_quiz_cat = selected_cat
        if 'flash_q' in st.session_state: del st.session_state.flash_q
        st.rerun()

    if 'flash_q' not in st.session_state:
        if selected_cat == "全部練習":
            pool = [{**v, "cat": c['category']} for c in data for g in c['root_groups'] for v in g['vocabulary']]
        else:
            pool = [{**v, "cat": c['category']} for c in data if c['category'] == selected_cat for g in c['root_groups'] for v in g['vocabulary']]
        if not pool: st.warning("此範圍無資料"); return
        st.session_state.flash_q = random.choice(pool)
        st.session_state.flipped = False
        st.session_state.voiced = False 

    q = st.session_state.flash_q
    
    # 單字卡片
    st.markdown(f"""
        <div style="text-align: center; padding: 5vh 2vw; border: 3px solid #eee; border-radius: 25px; background: #fdfdfd; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="color: #999; font-weight: bold;">[ {q['cat']} ]</p>
            <h1 class="responsive-word" style="margin: 0; color: #1E88E5;">{q['word']}</h1>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("查看答案", use_container_width=True): st.session_state.flipped = True
    with col2:
        if st.button("播放發音", use_container_width=True): speak(q['word'])
    with col3:
        if st.button("➡️ 下一題", use_container_width=True): 
            if 'flash_q' in st.session_state: del st.session_state.flash_q
            st.rerun()

    if st.session_state.get('flipped'):
        if not st.session_state.get('voiced'):
            speak(q['word'])
            st.session_state.voiced = True
        
        is_legal = "法律" in q['cat']
        bg_color, label_color, text_color, breakdown_color = ("#1A1A1A", "#FFD700", "#FFFFFF", "#FFD700") if is_legal else ("#E3F2FD", "#1E88E5", "#000000", "#D32F2F")
        p_val = str(q.get('phonetic', '')).strip().replace('/', '')
        phonetic_html = f"<div style='color:{label_color}; font-size:1.2em; margin-bottom:5px;'>/{p_val}/</div>" if p_val and p_val != "nan" else ""
        e_val, t_val = str(q.get('example', '')).strip(), str(q.get('translation', '')).strip()
        example_html = f"<hr style='border-color:#555; margin:15px 0;'><div style='font-style:italic; color:#666;' class='responsive-text'>{e_val}</div>" if e_val and e_val != "nan" else ""
        if t_val and t_val != "nan": example_html += f"<div style='color:#666; font-size:0.95em; margin-top:5px;'>({t_val})</div>"

        st.markdown(f"""
            <div style="background-color:{bg_color}; padding:25px; border-radius:15px; border-left:10px solid {label_color}; margin-top:20px;">
                {phonetic_html}
                <div class="responsive-text" style="color:{text_color};">
                    <strong style="color:{label_color};">拆解：</strong>
                    <span style="color:{breakdown_color}; font-family:monospace; font-weight:bold;">{q['breakdown']}</span>
                </div>
                <div class="responsive-text" style="color:{text_color}; margin-top:10px;">
                    <strong style="color:{label_color};">釋義：</strong> {q['definition']}
                </div>
                {example_html}
            </div>
        """, unsafe_allow_html=True)

def ui_search_page(data, selected_cat):
    st.title("搜尋與瀏覽")
    relevant = data if selected_cat == "全部顯示" else [c for c in data if c['category'] == selected_cat]
    query = st.text_input("搜尋單字或字根...").strip().lower()
    for cat in relevant:
        for group in cat.get('root_groups', []):
            matched = [v for v in group['vocabulary'] if query in v['word'].lower() or any(query in r.lower() for r in group['roots'])]
            if matched:
                with st.expander(f"{'/'.join(group['roots'])} ({group['meaning']})", expanded=bool(query)):
                    for v in matched:
                        st.markdown(f"**{v['word']}** [{v['breakdown']}]: {v['definition']}")

def ui_admin_page(data):
    st.title("🛡️ 管理區 (Cloud Admin)")
    correct_password = st.secrets.get("admin_password", "8787")
    if not st.session_state.get('admin_auth'):
        pw_input = st.text_input("管理員密碼", type="password")
        if pw_input == correct_password:
            st.session_state.admin_auth = True
            st.rerun()
        elif pw_input != "": st.error("密碼錯誤")
        return
    st.metric("資料庫單字總量", f"{get_stats(data)[1]} 單字")
    if st.button("手動備份 CSV"):
        flat = [{"category": c['category'], "roots": "/".join(g['roots']), "meaning": g['meaning'], **v} for c in data for g in c['root_groups'] for v in g['vocabulary']]
        st.download_button("確認下載 CSV", pd.DataFrame(flat).to_csv(index=False).encode('utf-8-sig'), "etymon_backup.csv")
    st.divider()
    st.subheader("📝 雲端待處理回報")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_pending = conn.read(spreadsheet=FEEDBACK_URL)
        if not df_pending.empty:
            st.dataframe(df_pending, use_container_width=True)
            if st.button("重新整理雲端數據"): st.rerun()
        else: st.info("目前沒有待處理的回報。")
    except Exception as e: st.error(f"讀取雲端回報失敗: {e}")
    if st.sidebar.button("登出管理區"):
        st.session_state.admin_auth = False
        st.rerun()

# ==========================================
# 3. 主程序入口
# ==========================================
def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    inject_custom_css() # 新增：注入自適應樣式
    data = load_db()
    st.sidebar.title("Etymon Decoder")
    menu = st.sidebar.radio("導航", ["字根區", "學習區", "國小區", "國中區", "高中區", "醫學區", "法律區", "人工智慧區", "心理與社會區", "生物與自然區", "管理區"], key="main_navigation")
    st.sidebar.divider()
    if st.sidebar.button("強制刷新雲端數據", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    _, total_words = get_stats(data)
    st.sidebar.markdown(f'<div style="text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;">資料庫總計<br><b>{total_words} Words</b></div>', unsafe_allow_html=True)

    # 路由邏輯 (保留原功能)
    if menu == "字根區":
        cats = ["全部顯示"] + sorted(list(set(c['category'] for c in data)))
        ui_search_page(data, st.sidebar.selectbox("分類篩選", cats))
    elif menu == "學習區": ui_quiz_page(data)
    elif menu == "國小區":
        elem = [c for c in data if any(k in str(c.get('category','')) for k in ["國小", "Elementary"])]
        ui_domain_page(elem, f"國小基礎字根 ({sum(len(g['vocabulary']) for c in elem for g in c['root_groups'])} 字)", "#FB8C00", "#FFF3E0")
    elif menu == "國中區":
        jhs = [c for c in data if any(k in str(c.get('category','')) for k in ["國中", "Junior"])]
        ui_domain_page(jhs, f"國中基礎字根 ({sum(len(g['vocabulary']) for c in jhs for g in c['root_groups'])} 字)", "#00838F", "#E0F7FA")
    elif menu == "高中區":
        hs = [c for c in data if any(k in str(c.get('category','')) for k in ["高中", "7000"])]
        ui_domain_page(hs, f"高中核心字根 ({sum(len(g['vocabulary']) for c in hs for g in c['root_groups'])} 字)", "#2E7D32", "#E8F5E9")
    elif menu == "醫學區":
        med = [c for c in data if "醫學" in str(c.get('category',''))]
        ui_domain_page(med, f"醫學專業字根 ({sum(len(g['vocabulary']) for c in med for g in c['root_groups'])} 字)", "#C62828", "#FFEBEE")
    elif menu == "法律區":
        law = [c for c in data if "法律" in str(c.get('category',''))]
        ui_domain_page(law, f"法律術語字根 ({sum(len(g['vocabulary']) for c in law for g in c['root_groups'])} 字)", "#FFD700", "#1A1A1A")
    elif menu == "人工智慧區":
        ai = [c for c in data if any(k in str(c.get('category','')) for k in ["人工智慧", "AI","資工"])]
        ui_domain_page(ai, f"人工智慧相關字根 ({sum(len(g['vocabulary']) for c in ai for g in c['root_groups'])} 字)", "#1565C0", "#E3F2FD")
    elif menu == "心理與社會區":
        psy = [c for c in data if any(k in str(c.get('category','')) for k in ["心理", "社會", "Psych", "Soc"])]
        ui_domain_page(psy, f"心理與社會科學字根 ({sum(len(g['vocabulary']) for c in psy for g in c['root_groups'])} 字)", "#AD1457", "#FCE4EC")
    elif menu == "生物與自然區":
        bio = [c for c in data if any(k in str(c.get('category','')) for k in ["生物", "自然", "科學", "Bio", "Sci"])]
        ui_domain_page(bio, f"生物與自然科學字根 ({sum(len(g['vocabulary']) for c in bio for g in c['root_groups'])} 字)", "#2E7D32", "#E8F5E9")
    elif menu == "管理區": ui_admin_page(data)

if __name__ == "__main__":
    main()
