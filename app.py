import streamlit as st
import json
import os
import random

# ==========================================
# 1. 核心配置
# ==========================================
DB_FILE = 'etymon_database.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
    return []

def get_stats(data):
    total_cats = len(data)
    total_words = sum(len(g.get('vocabulary', [])) for cat in data for g in cat.get('root_groups', []))
    return total_cats, total_words

# ==========================================
# 2. UI 組件
# ==========================================
def ui_search_page(data, selected_cat):
    st.title("字根導覽")
    
    # 1. 根據大類過濾
    relevant_cats = data if selected_cat == "全部顯示" else [c for c in data if c['category'] == selected_cat]
    
    root_options = []
    root_to_group = {}
    for cat in relevant_cats:
        for group in cat.get('root_groups', []):
            label = f"{' / '.join(group['roots'])} ({group['meaning']})"
            root_options.append(label)
            root_to_group[label] = (cat['category'], group)
    
    # 2. 字根快選
    selected_root_label = st.selectbox(f"字根選單 ({selected_cat})", ["顯示全部"] + root_options)
    
    st.divider()

    # 3. 顯示邏輯 (移除所有 random.choice 相關代碼)
    if selected_root_label == "顯示全部":
        query = st.text_input("檢索單字", placeholder="在目前範圍內搜尋...").lower().strip()
        for label in root_options:
            cat_name, group = root_to_group[label]
            matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()] if query else group['vocabulary']
            
            if matched_v:
                st.markdown(f"### {label}")
                for v in matched_v:
                    # 確保 is_expanded 是布林值
                    with st.expander(f"{v['word']}", expanded=bool(query)):
                        st.write(f"結構: `{v['breakdown']}`")
                        st.write(f"釋義: {v['definition']}")
    else:
        # 顯示單一字根組
        cat_name, group = root_to_group[selected_root_label]
        st.subheader(f"分類：{cat_name}")
        for v in group['vocabulary']:
            with st.expander(f"{v['word']}", expanded=False):
                st.write(f"結構: `{v['breakdown']}`")
                st.write(f"釋義: {v['definition']}")
def ui_quiz_page(data):
    # 0. 基礎狀態初始化
    if 'failed_words' not in st.session_state:
        st.session_state.failed_words = set()
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False

    # 1. 初始設定畫面
    if not st.session_state.quiz_active:
        st.title("記憶卡片")
        categories = ["全部隨機"] + sorted([c['category'] for c in data])
        selected_quiz_cat = st.selectbox("選擇練習範圍", categories)
        
        st.divider()
        if st.button("開始練習", use_container_width=True):
            st.session_state.selected_quiz_cat = selected_quiz_cat
            st.session_state.quiz_active = True
            st.rerun()
        return

    # 2. 練習模式：篩選與抽題
    st.title("記憶卡片")
    
    # 點擊結束按鈕
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.caption(f"目前範圍: {st.session_state.selected_quiz_cat}")
    if col_t2.button("結束", use_container_width=True):
        st.session_state.quiz_active = False
        if 'flash_q' in st.session_state: del st.session_state.flash_q
        st.rerun()

    # 準備題目池
    if st.session_state.selected_quiz_cat == "全部隨機":
        relevant_data = data
    else:
        relevant_data = [c for c in data if c['category'] == st.session_state.selected_quiz_cat]

    all_words = [{**v, "cat": cat['category']} for cat in relevant_data for group in cat.get('root_groups', []) for v in group.get('vocabulary', [])]

    if not all_words:
        st.warning("查無單字。")
        if st.button("返回"):
            st.session_state.quiz_active = False
            st.rerun()
        return

    if 'flash_q' not in st.session_state:
        st.session_state.flash_q = random.choice(all_words)
        st.session_state.is_flipped = False

    q = st.session_state.flash_q
    
    # 1. 智慧抽題邏輯 (50% 機率抽陌生字)
    if 'flash_q' not in st.session_state:
        if st.session_state.failed_words and random.random() > 0.5:
            # 從當前範圍 (all_words) 中找出屬於陌生清單的字
            failed_pool = [w for w in all_words if w['word'] in st.session_state.failed_words]
            if failed_pool:
                st.session_state.flash_q = random.choice(failed_pool)
                st.session_state.is_review = True
            else:
                st.session_state.flash_q = random.choice(all_words)
                st.session_state.is_review = False
        else:
            st.session_state.flash_q = random.choice(all_words)
            st.session_state.is_review = False
        st.session_state.is_flipped = False

    q = st.session_state.flash_q
    # 建立複習標籤的 HTML
    if is_review:
        # 使用淡紅色背景和深紅文字，做出標籤感
        review_tag = """
        <span style="
            background-color: #ffeef0; 
            color: #d73a49; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-size: 0.7rem; 
            font-weight: bold; 
            margin-left: 10px;
            border: 1px solid #f9c2c7;
        ">複習</span>
        """
    else:
        review_tag = ""

    # 在卡片正面渲染
    st.markdown(f"""
    <div class="flip-card">
      <div class="flip-card-inner {is_flipped_class}">
        <div class="flip-card-front">
          <div style="display: flex; align-items: center; justify-content: center;">
            <small style="color: #888; letter-spacing: 0.1em;">{q['cat'].upper()}</small>
            {review_tag}
          </div>
          <h1 style="font-size: 3.2rem; font-weight: 700; margin: 15px 0; color: #1a1a1a;">{q['word']}</h1>
          <div style="font-size: 0.7rem; color: #ccc; margin-top: 20px;">點擊翻轉</div>
        </div>
        ...
        <div class="flip-card-back">
          <div style="text-align: left; width: 100%;">
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">STRUCTURE</div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 1.1rem; color: #0366d6; margin-bottom: 24px;">{q['breakdown']}</div>
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">MEANING</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #24292e; line-height: 1.4;">{q['definition']}</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if not st.session_state.is_flipped:
        if st.button("查看答案", use_container_width=True):
            st.session_state.is_flipped = True
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        if c1.button("標記陌生", use_container_width=True):
            st.session_state.failed_words.add(q['word'])
            del st.session_state.flash_q
            st.rerun()
        if c2.button("標記熟練", use_container_width=True):
            st.session_state.failed_words.discard(q['word'])
            del st.session_state.flash_q
            st.rerun()
# ==========================================
# 3. 主程序
# ==========================================

def main():
    st.set_page_config(page_title="Etymon", layout="wide")
    data = load_db()
    
    st.sidebar.title("Etymon")
    
    # 導航功能
    menu_options = ["字根導覽", "記憶卡片"]
    choice = st.sidebar.radio("功能選單", menu_options)
    
    # 分類選單 (僅在導覽頁顯示，或作為全域過濾)
    st.sidebar.divider()
    categories = ["全部顯示"] + sorted([c['category'] for c in data])
    selected_cat = st.sidebar.selectbox("選擇分類", categories)
    
    # 數據統計
    c_count, w_count = get_stats(data)
    st.sidebar.divider()
    st.sidebar.write("**統計**")
    st.sidebar.text(f"分類總數: {c_count}")
    st.sidebar.text(f"單字總量: {w_count}")
    
    if choice == "字根導覽":
        ui_search_page(data, selected_cat)
    else:
        ui_quiz_page(data)
if __name__ == "__main__":
    main()
