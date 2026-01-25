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
            /* 1. 基礎字體比例加大 */
            html { font-size: 20px; } /* 整體基準點從 16px 提升 */

            /* 2. 手機端 (大字體優化) */
            @media (max-width: 600px) {
                .responsive-word { font-size: 15vw !important; margin-bottom: 10px; }
                .responsive-breakdown { font-size: 6vw !important; padding: 10px 15px !important; }
                .responsive-text { font-size: 5.5vw !important; line-height: 1.5; }
                .stButton button { height: 3.5rem; font-size: 1.2rem !important; }
            }

            /* 3. 電腦端 (清晰大字) */
            @media (min-width: 601px) {
                .responsive-word { font-size: 4rem !important; }
                .responsive-breakdown { font-size: 2rem !important; }
                .responsive-text { font-size: 1.5rem !important; }
            }

            /* 4. 構造拆解框：完全隨系統變色，不再寫死深色 */
            .breakdown-container {
                font-family: 'Courier New', monospace;
                font-weight: bold;
                background-color: var(--secondary-background-color); 
                color: var(--text-color); 
                padding: 12px 20px;
                border-radius: 12px;
                border: 2px solid var(--primary-color); /* 用主題色框出重點 */
                display: inline-block;
                margin: 10px 0;
            }

            /* 5. 側邊欄統計框：隨系統變色 */
            .stats-container {
                text-align: center; 
                padding: 20px; 
                background-color: var(--secondary-background-color); 
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 15px; 
                color: var(--text-color);
            }

            /* 6. 禁止 Selectbox 輸入並加強 Pill 按鈕視覺 */
            .stSelectbox div[role="button"] input { caret-color: transparent !important; pointer-events: none !important; }
            
            div[data-testid="stPills"] button {
                font-size: 1.1rem !important;
                padding: 8px 16px !important;
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
    # 定義 9 欄一組的範圍
    BLOCKS = ["A:I", "J:R", "S:AA", "AB:AJ", "AK:AS"]
    COL_NAMES = [
        'category', 'roots', 'meaning', 'word', 
        'breakdown', 'definition', 'phonetic', 'example', 'translation'
    ]
    
    all_dfs = []
    for rng in BLOCKS:
        try:
            url = f"{GSHEET_URL}&range={rng}"
            # 重點：使用 skiprows=1 避開標題列，並手動指定欄位名稱
            df_part = pd.read_csv(url, skiprows=1, names=COL_NAMES)
            
            # 清理資料：移除全空的列，並確保 category 欄位有值
            df_part = df_part.dropna(subset=['category', 'word'], how='all')
            
            if not df_part.empty:
                all_dfs.append(df_part)
        except Exception as e:
            continue

    if not all_dfs: return []
    df = pd.concat(all_dfs, ignore_index=True)
    
    # 結構化處理
    structured_data = []
    # 移除可能重複讀入標題字串的異常資料 (保險機制)
    df = df[df['category'] != 'category'] 
    
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
            root_groups.append({
                "roots": [r.strip() for r in str(roots).split('/')],
                "meaning": str(meaning),
                "vocabulary": vocabulary
            })
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
    # --- 任務 1：使用說明介面 ---
    with st.expander("📖 初次使用？點擊查看「拆解式學習法」說明", expanded=False):
        st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background-color:{bg_color}22; border-left:5px solid {theme_color};">
            <h4 style="color:{theme_color}; margin-top:0;">如何使用此工具？</h4>
            <ol class="responsive-text">
                <li><b>搜尋字根：</b> 在下方輸入框輸入你想找的字根（如 <code>bio</code>）或含義（如 <code>生命</code>）。</li>
                <li><b>觀察構造：</b> 點開單字後，重點看「構造拆解」，理解前綴、字根、後綴如何組合成新字。</li>
                <li><b>聽音記憶：</b> 點擊「播放」按鈕，結合發音與拆解能大幅提升記憶深度。</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<h1 class="responsive-title">{title}</h1>', unsafe_allow_html=True)
    
    # 建立字根映射表
    root_map = {}
    for cat in domain_data:
        for group in cat.get('root_groups', []):
            label = f"{'/'.join(group['roots'])} ({group['meaning']})"
            root_map[label] = group
    
    # --- 任務 2：刪除按鈕，改為輸入搜尋框 ---
    search_query = st.text_input("輸入字根或含義進行篩選", placeholder="例如：act, bio, 動作, 生命...")
    
    # 根據輸入內容篩選字根
    filtered_labels = [
        label for label in root_map.keys() 
        if search_query.lower() in label.lower()
    ]

    if search_query:
        if filtered_labels:
            for label in filtered_labels:
                group = root_map[label]
                with st.expander(f"字根：{label}", expanded=True):
                    for v in group.get('vocabulary', []):
                        st.markdown(f'<div class="responsive-word" style="font-weight:bold; color:{theme_color};">{v["word"]}</div>', unsafe_allow_html=True)
                        
                        col_play, col_report, _ = st.columns([1, 1, 2])
                        with col_play:
                            if st.button("播放", key=f"s_{v['word']}_{label}"): speak(v['word'])
                        with col_report:
                            ui_feedback_component(v['word'])
                        
                        st.markdown(f"""
                            <div style="margin-top: 10px;">
                                <span class="responsive-text" style="opacity: 0.8;">構造拆解：</span><br>
                                <div class="breakdown-container responsive-breakdown">{v['breakdown']}</div>
                                <div class="responsive-text" style="margin-top: 10px;">
                                    <b>中文定義：</b> {v['definition']}
                                </div>
                            </div>
                            <hr style="margin: 20px 0; opacity: 0.1;">
                        """, unsafe_allow_html=True)
        else:
            st.info("找不到相關字根，請查明關鍵字。")
    else:
        st.caption("請在上方輸入框輸入字根開始探索。")
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
def ui_newbie_whiteboard():
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); padding: 25px; border-radius: 15px; border: 2px dashed var(--primary-color);">
        <h2 style="margin-top:0; text-align:center;">歡迎使用 Etymon Decoder</h2>
        <p style="text-align:center; opacity:0.8;">這是一個專為「拆解式學習」設計的工具，幫你從根本理解英文。</p>
        <hr>
        <h4 style="color:var(--primary-color);">1. 核心邏輯：拆解積木</h4>
        <p>英文單字是由積木組成的。例如：<b>Re (回) + Port (搬運) = Report (報告)</b>。</p>
    """, unsafe_allow_html=True)

    # 此處建議放入您提供的圖片 (例如單字結構圖)
    # st.image("path_to_your_image.png", caption="單字結構示範")
    

    st.markdown("""
        <h4 style="color:var(--primary-color);">2. 快速上手步驟</h4>
        <ul class="responsive-text">
            <li><b>第一步：鎖定領域</b> - 從左側選單選擇適合你的程度（如：國中區）。</li>
            <li><b>第二步：精準搜尋</b> - 在搜尋框輸入字根 (如 <code>bio</code>) 或含義 (如 <code>生命</code>)。</li>
            <li><b>第三步：聽音看拆解</b> - 點開結果，觀看拆解公式並點擊播放聆聽發音。</li>
        </ul>
        <h4 style="color:var(--primary-color);">3. 找不到想搜尋的？</h4>
        <p>往左下角看！側邊欄有<b>「分類篩選」</b>，可以快速瀏覽特定學科的單字庫。</p>
    </div>
    """, unsafe_allow_html=True)
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
    # --- 任務 1：標題與使用說明彈窗 ---
    col_title, col_help = st.columns([3, 1])
    with col_title:
        st.markdown('<h1 class="responsive-title">搜尋與瀏覽</h1>', unsafe_allow_html=True)
    with col_help:
        # 在主介面右上角放一個顯眼的說明按鈕
        with st.popover("📖 使用教學", use_container_width=True):
            ui_newbie_whiteboard() # 呼叫任務 3 的白板

    # 篩選分類
    relevant = data if selected_cat == "全部顯示" else [c for c in data if c['category'] == selected_cat]
    
    # --- 任務 2：純搜尋模式 (無按鈕) ---
    st.markdown("### 🔍 快速搜尋")
    query = st.text_input(
        "輸入字根或含義", 
        placeholder="例如：act, bio, 動作, 生命...", 
        key="global_search_input"
    ).strip().lower()
    
    if not query:
        # --- 任務 3：新手進入時看到的白板引導 ---
        st.info("💡 提示：請在上方搜尋框輸入關鍵字，或使用側邊欄的「分類篩選」縮小範圍。")
        ui_newbie_whiteboard()
        return

    # 執行搜尋邏輯
    found_results = False
    for cat in relevant:
        for group in cat.get('root_groups', []):
            # 檢查字根或單字是否匹配
            matched_vocab = [
                v for v in group['vocabulary'] 
                if query in v['word'].lower() or any(query in r.lower() for r in group['roots'])
            ]
            
            if matched_vocab:
                found_results = True
                root_label = f"{'/'.join(group['roots'])} ({group['meaning']})"
                with st.expander(f"✨ {cat['category']} | {root_label}", expanded=True):
                    for v in matched_vocab:
                        st.markdown(f'<div class="responsive-word" style="color:var(--primary-color); font-weight:bold;">{v["word"]}</div>', unsafe_allow_html=True)
                        
                        c1, c2, _ = st.columns([1, 1, 2])
                        with c1:
                            if st.button("播放", key=f"p_{v['word']}_{cat['category']}"): speak(v['word'])
                        with c2:
                            ui_feedback_component(v['word'])
                        
                        st.markdown(f"""
                            <div class="breakdown-container responsive-breakdown">{v['breakdown']}</div>
                            <div class="responsive-text"><b>中文定義：</b> {v['definition']}</div>
                            <hr style="opacity:0.1; margin:15px 0;">
                        """, unsafe_allow_html=True)
    
    if not found_results:
        st.warning("找不到匹配的字根或單字，請嘗試換個關鍵字。")
def ui_admin_page(data):
    st.title("管制區")
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
    st.subheader("雲端待處理回報")
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
    inject_custom_css() 
    data = load_db()
    
    # 1. 側邊欄：導航菜單 (決定 menu 變數)
    st.sidebar.title("Etymon Decoder")
    menu = st.sidebar.radio(
        "導航", 
        ["字根區", "學習區", "國小區", "國中區", "高中區", "醫學區", "法律區", "人工智慧區", "心理與社會區", "生物與自然區", "管理區"], 
        key="nav_menu" # 確保 key 固定
    )
    
    st.sidebar.divider()

    # 任務 1：側欄說明按鈕 (截圖 6.09.18 左側)
    with st.sidebar.expander("📖 使用說明 (新手必看)", expanded=False):
        st.info("歡迎使用！請先選擇導航頻道，再配合下方分類篩選開始學習。")
        # 這裡可以放簡短版說明

    # 強制刷新按鈕
    if st.sidebar.button("強制刷新雲端數據", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()

    # 資料庫統計
    _, total_words = get_stats(data)
    st.sidebar.markdown(f"""
        <div class="stats-container">
            <p style="margin: 0; font-size: 0.8em; opacity: 0.7;">資料庫總計</p>
            <p style="margin: 0; font-size: 1.5em; font-weight: bold;">{total_words} Words</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. 分類篩選 (僅在字根區或其他分區時顯示)
    st.sidebar.subheader("分類篩選")
    cats = ["全部顯示", "國小基礎", "專業心理", "專業法律", "專業生物", "專業資工", "專業醫學", "進階高中", "高中必備"]
    # 根據實際 data 取得動態分類或使用固定分類
    selected_cat = st.sidebar.radio("選擇領域", cats, key="domain_filter")
    st.sidebar.caption("💡 技巧：往下選取不同領域以篩選單字。")

    # --- 3. 關鍵路由邏輯：確保頁面內容隨 menu 切換 ---
    st.divider() # 裝飾用

    if menu == "字根區":
        # 任務 2：呼叫搜尋介面
        ui_search_page(data, selected_cat)
        
    elif menu == "學習區": 
        ui_quiz_page(data)
        
    else:
        # 其他分區：根據選中的 menu 篩選數據
        # 建立對應表
        mapping = {
            "國小區": "國小", "國中區": "國中", "高中區": "高中", 
            "醫學區": "醫學", "法律區": "法律", "人工智慧區": "資工",
            "心理與社會區": "心理", "生物與自然區": "生物"
        }
        
        target_key = mapping.get(menu, "")
        domain_data = [c for c in data if target_key in str(c.get('category',''))]
        
        # 設定不同色調
        theme_colors = {"法律區": "#FFD700", "醫學區": "#C62828", "國小區": "#FB8C00"}
        current_color = theme_colors.get(menu, "#1E88E5")
        
        ui_domain_page(domain_data, f"{menu}內容", current_color, "#F0F2F6")

# 確保在檔案最下方呼叫
if __name__ == "__main__":
    main()
