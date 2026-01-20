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
    
    # 1. 整理選單資料：根據側邊欄選擇的大類來決定字根清單
    relevant_cats = data if selected_cat == "全部顯示" else [c for c in data if c['category'] == selected_cat]
    
    root_options = []
    root_to_group = {}
    
    for cat in relevant_cats:
        for group in cat['root_groups']:
            # 建立選單標籤：字根 (含義)
            label = f"{' / '.join(group['roots'])} ({group['meaning']})"
            root_options.append(label)
            root_to_group[label] = (cat['category'], group)
    
    # 2. 字根快選選單 (預設列出全部，除非側邊欄有選大類)
    selected_root_label = st.selectbox(
        f"字根選單 (目前範圍: {selected_cat})", 
        ["顯示全部"] + root_options
    )
    
    st.divider()

    # 3. 核心顯示邏輯
    if selected_root_label == "顯示全部":
        # 如果選顯示全部，就列出目前範圍內所有的字根與單字
        query = st.text_input("檢索單字", placeholder="在目前範圍內搜尋...").lower().strip()
        
        for label in root_options:
            cat_name, group = root_to_group[label]
            
            # 檢查單字過濾
            matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()] if query else group['vocabulary']
            
            if matched_v:
                st.markdown(f"### {label}")
                for v in matched_v:
                    is_expanded = bool(query) # 有搜尋才展開
                    with st.expander(f"{v['word']}", expanded=is_expanded):
                        st.write(f"結構: `{v['breakdown']}`")
                        st.write(f"釋義: {v['definition']}")
    else:
        # 如果選了特定字根，只顯示該組內容
        cat_name, group = root_to_group[selected_root_label]
        st.subheader(f"分類：{cat_name}")
        st.info(f"字根：{selected_root_label}")
        
        for v in group['vocabulary']:
            with st.expander(f"{v['word']}", expanded=False):
                st.write(f"結構: `{v['breakdown']}`")
                st.write(f"釋義: {v['definition']}")
# 頂部工具列：顯示目前範圍與退出按鈕
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.caption(f"範圍: {st.session_state.selected_quiz_cat}")
    
    # 移除 size="small" 參數，改用標準按鈕
    if col_t2.button("結束", use_container_width=True):
        st.session_state.quiz_active = False
        if 'flash_q' in st.session_state:
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
