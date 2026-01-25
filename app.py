import streamlit as st
import json
import os
import random
import pandas as pd
from gtts import gTTS
import time
import base64
from io import BytesIO
from gtts import gTTS
from streamlit_gsheets import GSheetsConnection
# ==========================================
# 1. 修正語音發音 (確保有聲音且 autoplay)
# ==========================================
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode()
        
        # 使用隨機 ID 避免 Streamlit 元件快取
        cid = f"aud_{int(time.time()*1000)}"
        audio_html = f"""
            <audio autoplay id="{cid}">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>
                var x = document.getElementById("{cid}");
                x.volume = 1.0;
                x.play().catch(function(e) {{ console.log("Autoplay blocked"); }});
            </script>
            """
        # height=0 隱藏 HTML 元件空間
        st.components.v1.html(audio_html, height=0)
    except Exception as e:
        st.error(f"語音生成失敗: {e}")
# ==========================================
# 1. 核心配置與雲端同步
# ==========================================

# 這是你原本「唯讀」的單字庫資料來源
SHEET_ID = '1Gs0FX7c8bUQTnSytX1EqjMLATeVc30GmdjSOYW_sYsQ'
GSHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
PENDING_FILE = 'pending_data.json'
# 這是你要「寫入」回報的目標網址 (從 secrets 讀取)
FEEDBACK_URL = st.secrets.get("feedback_sheet_url")
@st.cache_data(ttl=600)
def load_db():
    import string
    # A=0, B=11, C=22, D=33... 這是對應您 A-Z 橫向並排的索引
    ALPHABET = list(string.ascii_uppercase)
    BLOCK_MAP = {letter: i * 11 for i, letter in enumerate(ALPHABET)}
    
    try:
        # 讀取完整試算表，確保不漏掉任何欄位
        raw_df = pd.read_csv(GSHEET_URL)
        if raw_df.empty:
            return []
    except Exception as e:
        st.error(f"讀取試算表失敗: {e}")
        return []

    structured_data = []
    total_word_count = 0

    for letter, start_idx in BLOCK_MAP.items():
        # 檢查該區塊是否存在於試算表中
        if start_idx + 3 >= len(raw_df.columns): 
            continue
            
        try:
            # 擷取該字母區塊的 9 欄
            df_part = raw_df.iloc[:, start_idx:start_idx+9].copy()
            df_part.columns = [
                'category', 'roots', 'meaning', 'word', 
                'breakdown', 'definition', 'phonetic', 'example', 'translation'
            ]
            
            # 清理資料：移除標題行，並確保 'word' 欄位有內容
            df_part = df_part[df_part['word'].notna()]
            df_part = df_part[df_part['word'].astype(str).str.lower() != 'word']
            df_part = df_part[df_part['category'].astype(str).str.lower() != 'category']

            if df_part.empty:
                continue

            sub_cats = []
            # 第一層：依據 Category (小分支) 分組
            for cat_name, cat_group in df_part.groupby('category'):
                root_groups = []
                # 第二層：依據 Roots 分組
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
                            total_word_count += 1
                    
                    if vocabulary:
                        root_groups.append({
                            "roots": [r.strip() for r in str(roots).split('/')],
                            "meaning": str(meaning),
                            "vocabulary": vocabulary
                        })
                
                if root_groups:
                    sub_cats.append({
                        "name": str(cat_name),
                        "root_groups": root_groups
                    })
            
            if sub_cats:
                structured_data.append({
                    "letter": letter,
                    "sub_categories": sub_cats
                })
        except Exception:
            continue
            
    return structured_data
def save_feedback_to_gsheet(word, feedback_type, comment):
    try:
        # 1. 建立連線
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 2. 強制不使用快取讀取資料 (ttl=0)
        df = conn.read(spreadsheet=FEEDBACK_URL, ttl=0)
        
        # 2. 建立新資料列
        new_row = pd.DataFrame([{
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "word": word,
            "type": feedback_type,
            "comment": comment,
            "status": "pending"
        }])
        
        # 3. 合併並更新
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # 4. 執行寫入 (關鍵：這一步需要 Service Account 權限)
        conn.update(spreadsheet=FEEDBACK_URL, data=updated_df)
        
        st.success(f"✅ 單字「{word}」的回報已同步至雲端！")
        
    except Exception as e:
        # 如果還是噴錯，顯示更詳細的訊息
        st.error(f"❌ 雲端同步失敗。")
        st.info("請檢查 Streamlit Cloud 的 Secrets 是否已包含完整的 [connections.gsheets] 區段內容。")
        st.caption(f"錯誤詳情: {e}")
def get_stats(data):
    """計算單字總數"""
    if not data: return 0, 0
    total_words = sum(len(g.get('vocabulary', [])) for cat in data for g in cat.get('root_groups', []))
    return len(data), total_words
# ==========================================
# 2. 通用與專業區域組件
# ==========================================
def render_word_card(v, title, theme_color):
    display_color = "#FFD700" if "法律" in title else theme_color
    
    # 使用 st.container 增加間距
    with st.container(border=True):
        col_w, col_p, col_r = st.columns([3, 1, 1])
        with col_w:
            st.markdown(f'<div style="font-size: 1.8em; font-weight: bold; color: {display_color};">{v["word"]}</div>', unsafe_allow_html=True)
            if v.get('phonetic'):
                st.caption(f"/{v['phonetic']}/")
        
        with col_p:
            if st.button("🔊 播放", key=f"btn_p_{v['word']}_{title}"):
                speak(v['word'])
        
        with col_r:
            ui_feedback_component(v['word'])

        # 拆解與定義區
        st.markdown(f"""
            <div style="margin-top: 10px; padding: 10px; background: rgba(100,100,100,0.1); border-radius: 8px;">
                <span style="color: #888; font-size: 0.9em;">構造：</span>
                <code style="color: #FFD700; font-size: 1.2em; font-weight: bold;">{v['breakdown']}</code>
                <div style="margin-top: 5px;"><b>定義：</b> {v['definition']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if v.get('example'):
            with st.expander("查看例句"):
                st.write(f"*{v['example']}*")
                if v.get('translation'):
                    st.caption(f"({v['translation']})")
def ui_feedback_component(word):
    """單字錯誤回報彈窗"""
    with st.popover("錯誤回報"):
        st.write(f"回報單字：**{word}**")
        f_type = st.selectbox("錯誤類型", ["發音錯誤", "拆解有誤", "中文釋義錯誤", "分類錯誤", "其他"], key=f"err_type_{word}")
        f_comment = st.text_area("詳細說明", placeholder="請描述正確的資訊...", key=f"err_note_{word}")
        
        if st.button("提交回報", key=f"err_btn_{word}"):
            if f_comment.strip() == "":
                st.error("請填寫說明內容")
            else:
                save_feedback_to_gsheet(word, f_type, f_comment)
                st.success("感謝回報！管理員將會盡快修正。")
def ui_quiz_page(data):
    st.title("學習區 (Flashcards)")
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
    
    # 單字卡片正面
    st.markdown(f"""
        <div style="text-align: center; padding: 50px; border: 3px solid #eee; border-radius: 25px; background: #fdfdfd; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="color: #999; font-weight: bold;">[ {q['cat']} ]</p>
            <h1 style="font-size: 4.5em; margin: 0; color: #1E88E5;">{q['word']}</h1>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("查看答案", use_container_width=True): 
            st.session_state.flipped = True
    with col2:
        if st.button("播放發音", use_container_width=True):
            speak(q['word'])
    with col3:
        if st.button("➡️ 下一題", use_container_width=True): 
            if 'flash_q' in st.session_state: del st.session_state.flash_q
            st.rerun()

    # 答案翻開後的邏輯
    if st.session_state.get('flipped'):
        if not st.session_state.get('voiced'):
            speak(q['word'])
            st.session_state.voiced = True
            
        is_legal = "法律" in q['cat']
        bg_color = "#1A1A1A" if is_legal else "#E3F2FD"
        label_color = "#FFD700" if is_legal else "#1E88E5"
        text_color = "#FFFFFF" if is_legal else "#000000"
        breakdown_color = "#FFD700" if is_legal else "#D32F2F"

        # 處理音標：移除多餘斜線
        p_val = str(q.get('phonetic', '')).strip().replace('/', '')
        phonetic_html = f"<div style='color:{label_color}; font-size:1.2em; margin-bottom:5px;'>/{p_val}/</div>" if p_val and p_val != "nan" else ""
        
        # 處理例句與翻譯：直接組合成字串，不使用多行引號以減少錯誤
        e_val = str(q.get('example', '')).strip()
        t_val = str(q.get('translation', '')).strip()
        
        example_html = ""
        if e_val and e_val != "nan":
            # 這裡改用最簡單的字串相加，避免縮排問題
            example_html += f"<hr style='border-color:#555; margin:15px 0;'>"
            example_html += f"<div style='font-style:italic; color:#666; font-size:1.1em;'>{e_val}</div>"
            if t_val and t_val != "nan":
                example_html += f"<div style='color:#666; font-size:0.95em; margin-top:5px;'>({t_val})</div>"

        # 最終渲染：確保 full_html 變數完全左對齊，沒有任何空格縮排
        full_html = f"""
<div style="background-color:{bg_color}; padding:25px; border-radius:15px; border:1px solid {label_color}; border-left:10px solid {label_color}; margin-top:20px;">
{phonetic_html}
<div style="font-size:2em; margin-bottom:10px; color:{text_color};">
<strong style="color:{label_color};">拆解：</strong>
<span style="color:{breakdown_color}; font-family:monospace; font-weight:bold;">{q['breakdown']}</span>
</div>
<div style="font-size:1.5em; color:{text_color};">
<strong style="color:{label_color};">釋義：</strong> {q['definition']}
</div>
{example_html}
</div>
"""
        st.markdown(full_html, unsafe_allow_html=True)
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
    
    # 1. 密碼驗證 (使用 st.secrets)
    correct_password = st.secrets.get("admin_password", "8787")
    if not st.session_state.get('admin_auth'):
        pw_input = st.text_input("管理員密碼", type="password")
        if pw_input == correct_password:
            st.session_state.admin_auth = True
            st.rerun()
        elif pw_input != "":
            st.error("密碼錯誤")
        return

    # 2. 數據統計
    st.metric("資料庫單字總量", f"{get_stats(data)[1]} 單字")
    
    # 3. 備份功能
    if st.button("手動備份 CSV (下載完整單字庫)"):
        flat = [{"category": c['category'], "roots": "/".join(g['roots']), "meaning": g['meaning'], **v} 
                for c in data for g in c['root_groups'] for v in g['vocabulary']]
        st.download_button("確認下載 CSV", pd.DataFrame(flat).to_csv(index=False).encode('utf-8-sig'), "etymon_backup.csv")

    st.divider()

    # 4. 讀取雲端回報 (取代舊的 PENDING_FILE 邏輯)
    st.subheader("📝 雲端待處理回報")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 使用你在 Section 1 定義的 FEEDBACK_URL
        df_pending = conn.read(spreadsheet=FEEDBACK_URL)
        
        if not df_pending.empty:
            st.dataframe(df_pending, use_container_width=True)
            
            st.info("💡 提示：如需修改或刪除回報，請直接前往 Google Sheets 進行操作。")
            if st.button("重新整理雲端數據"):
                st.rerun()
        else:
            st.info("目前沒有待處理的回報。")
    except Exception as e:
        st.error(f"讀取雲端回報失敗，請檢查 Service Account 權限與 FEEDBACK_URL。")
        st.caption(f"錯誤詳情: {e}")

    # 5. 登出
    if st.sidebar.button("登出管理區"):
        st.session_state.admin_auth = False
        st.rerun()
# ==========================================
# 3. 主程序入口
# ==========================================
def main():
    st.set_page_config(page_title="Etymon Decoder", layout="wide")
    data = load_db()
    
    # 1. 側邊欄標題
    st.sidebar.title("tymon Decoder")
    
    # 2. 導覽選單
    menu = st.sidebar.radio("導航", ["字根區", "學習區", "高中 7000 區", "醫學區", "法律區", "人工智慧區", "心理與社會區", "生物與自然區", "管理區"])
    
    st.sidebar.divider()
    
    # 3. 強制刷新按鈕
    if st.sidebar.button("強制刷新雲端數據", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    
    # 4. 在刷新按鈕下方顯示單字總量 (使用大字體樣式)
    _, total_words = get_stats(data)
    st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px; margin-top: 10px;">
            <p style="margin: 0; font-size: 0.9em; color: #000;">資料庫總計</p>
            <p style="margin: 0; font-size: 1.8em; font-weight: bold; color: #000;">{total_words} <span style="font-size: 0.5em;">Words</span></p>
        </div>
    """, unsafe_allow_html=True)
# 在 main() 開頭計算總字數
    total_count = 0
    for block in data:
        for sub in block['sub_categories']:
            for group in sub['root_groups']:
                total_count += len(group['vocabulary'])

    # 更新側邊欄顯示 (取代原本的 0 Words)
    st.sidebar.metric("資料庫總計", f"{total_count} Words")

    if menu == "字根區":
        st.title("🗂️ 字根總覽 (A-Z 大區)")
        
        if total_count == 0:
            st.error("❌ 讀取不到單字。請確認試算表 A、D、O 欄等 Word 欄位是否有填寫內容。")
            return

        for block in data:
            with st.expander(f"✨ 字母區塊：{block['letter']}"):
                for sub in block['sub_categories']:
                    st.markdown(f"#### 📂 分類：{sub['name']}")
                    for group in sub['root_groups']:
                        st.info(f"**字根：** {' / '.join(group['roots'])} ({group['meaning']})")
                        # 顯示單字表格
                        display_df = [{"單字": v['word'], "解釋": v['definition'], "翻譯": v['translation']} for v in group['vocabulary']]
                        st.table(display_df)
if __name__ == "__main__":
    main()
