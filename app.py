import streamlit as st
import json
import os
import random

# ==========================================
# 1. 核心設定與數據加載
# ==========================================
DB_PATH = 'etymon_database.json'

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
    return []

# ==========================================
# 2. 字根導覽頁面
# ==========================================
def ui_search_page(data):
    st.title("字根導覽")
    query = st.text_input("檢索字根或單字", placeholder="例如: scrib, vis...").lower().strip()
    
    if query:
        found = False
        for cat in data:
            for group in cat['root_groups']:
                root_match = any(query in r.lower() for r in group['roots'])
                matched_v = [v for v in group['vocabulary'] if query in v['word'].lower()]
                if root_match or matched_v:
                    found = True
                    st.markdown(f"**{cat['category']}** ({' / '.join(group['roots'])})")
                    for v in group['vocabulary']:
                        is_target = query in v['word'].lower()
                        with st.expander(f"{v['word']}", expanded=is_target):
                            st.write(f"結構: `{v['breakdown']}`")
                            st.write(f"釋義: {v['definition']}")
        if not found: st.write("未找到匹配項")

# ==========================================
# 3. 記憶卡片頁面 (含陌生字邏輯)
# ==========================================
def ui_quiz_page(data):
    st.title("記憶卡片")
    
    # 初始化本地紀錄
    if 'failed_pool' not in st.session_state:
        st.session_state.failed_pool = []
    
    all_words = [{**v, "cat": cat['category']} for cat in data for group in cat['root_groups'] for v in group['vocabulary']]
    if not all_words: return st.write("數據庫空缺")
    
    # 抽題邏輯：若有陌生字，40% 機率抽陌生字進行複習
    if 'flash_q' not in st.session_state:
        if st.session_state.failed_pool and random.random() < 0.4:
            st.session_state.flash_q = random.choice(st.session_state.failed_pool)
        else:
            st.session_state.flash_q = random.choice(all_words)
        st.session_state.is_flipped = False
    
    q = st.session_state.flash_q
    is_flipped_class = "flipped" if st.session_state.is_flipped else ""

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    .flip-card { background-color: transparent; width: 100%; height: 350px; perspective: 1000px; font-family: 'Inter', sans-serif; }
    .flip-card-inner { position: relative; width: 100%; height: 100%; transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1); transform-style: preserve-3d; }
    .flipped { transform: rotateY(180deg); }
    .flip-card-front, .flip-card-back { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #ffffff; border: 1px solid #e1e4e8; }
    .flip-card-back { transform: rotateY(180deg); padding: 40px; border: 1.5px solid #d1d5da; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="flip-card">
      <div class="flip-card-inner {is_flipped_class}">
        <div class="flip-card-front">
          <div style="font-size: 0.75rem; color: #888; letter-spacing: 1px;">{q['cat']}</div>
          <h1 style="font-size: 3rem; font-weight: 700; margin: 10px 0; color: #1a1a1a;">{q['word']}</h1>
          <div style="font-size: 0.7rem; color: #ccc; margin-top: 30px;">TAP TO FLIP</div>
        </div>
        <div class="flip-card-back">
          <div style="text-align: left; width: 100%;">
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">結構</div>
            <div style="font-family: monospace; font-size: 1.1rem; color: #333; margin-bottom: 24px;">{q['breakdown']}</div>
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 4px;">釋義</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #222;">{q['definition']}</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if not st.session_state.is_flipped:
        if st.button("翻轉", use_container_width=True):
            st.session_state.is_flipped = True
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        if col1.button("標記陌生", use_container_width=True):
            if q not in st.session_state.failed_pool:
                st.session_state.failed_pool.append(q)
            del st.session_state.flash_q
            st.rerun()
        if col2.button("標記熟練", use_container_width=True):
            if q in st.session_state.failed_pool:
                st.session_state.failed_pool.remove(q)
            del st.session_state.flash_q
            st.rerun()
            
    if st.session_state.failed_pool:
        st.caption(f"待複習單字：{len(st.session_state.failed_pool)}")

# ==========================================
# 4. 主程序
# ==========================================
def main():
    st.set_page_config(page_title="Etymon", layout="wide")
    data = load_db()
    
    st.sidebar.title("Etymon")
    st.sidebar.caption("v1.1 精簡版")
    
    menu = {
        "字根導覽": lambda: ui_search_page(data),
        "記憶卡片": lambda: ui_quiz_page(data)
    }
    
    choice = st.sidebar.radio("選單", list(menu.keys()), label_visibility="collapsed")
    menu[choice]()

if __name__ == "__main__":
    main()
