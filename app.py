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
# ==========================================
# 4. 管理員功能 (含密碼保護)
# ==========================================

def ui_admin_page():
    st.title("🛠️ 數據管理後台")
    
    # --- 權限驗證 ---
    ADMIN_PASSWORD = "your_password_here"  # 👈 請在此設定你的密碼
    
    # 使用 session_state 紀錄登入狀態，避免每次操作都要重打密碼
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.info("此區域受密碼保護")
        pwd_input = st.text_input("請輸入管理員密碼", type="password")
        if st.button("登入"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("身分驗證成功！")
                st.rerun()
            else:
                st.error("密碼錯誤，請重新輸入。")
        return # 未通過驗證前，不執行後面的代碼

    # --- 通過驗證後的管理介面 ---
    col_header, col_logout = st.columns([4, 1])
    col_header.markdown("### 📥 數據導入與合併")
    if col_logout.button("登出管理台"):
        st.session_state.admin_authenticated = False
        st.rerun()

    st.markdown("在此貼上新的 JSON 數據，系統將自動去重並合併至資料庫。")

    # JSON 輸入區
    json_input = st.text_area("JSON 數據輸入", height=300, 
                             placeholder='{"category": "醫學術語", "root_groups": [...] }')
    
    col1, col2 = st.columns([1, 4])
    if col1.button("執行合併", type="primary"):
        if json_input.strip():
            try:
                pending_data = json.loads(json_input)
                # 呼叫之前寫好的 merge_logic 函數
                success, msg = merge_logic(pending_data) 
                if success:
                    st.success(f"✅ {msg}")
                    # 清除 Streamlit 快取以確保導覽頁看到最新數據
                    st.cache_data.clear() 
                else:
                    st.error(msg)
            except json.JSONDecodeError:
                st.error("❌ JSON 格式錯誤，請檢查括號、逗號與雙引號。")
        else:
            st.warning("⚠️ 請先輸入數據。")

    # 幫助說明
    with st.expander("查看醫學單字 JSON 結構範例"):
        st.code("""
{
  "category": "醫學術語",
  "root_groups": [
    {
      "roots": ["cardi-"],
      "meaning": "心臟",
      "vocabulary": [
        {"word": "Cardiology", "breakdown": "cardi- + -ology", "definition": "心臟病學"}
      ]
    }
  ]
}
        """, language="json")
def ui_admin_page():
    st.title("🛠️ 數據管理後台")
    st.markdown("在此貼上新的 JSON 數據，系統將自動去重並合併至資料庫。")

    # JSON 輸入區
    json_input = st.text_area("JSON 數據輸入", height=300, placeholder='{"category": "醫學", "root_groups": [...] }')
    
    col1, col2 = st.columns([1, 4])
    if col1.button("執行合併", type="primary"):
        if json_input.strip():
            try:
                pending_data = json.loads(json_input)
                success, msg = merge_logic(pending_data)
                if success:
                    st.success(msg)
                    # 重新計算統計數據
                    st.cache_data.clear() 
                else:
                    st.error(msg)
            except json.JSONDecodeError:
                st.error("JSON 格式錯誤，請檢查括號與引號。")
        else:
            st.warning("請先輸入數據。")

    with st.expander("查看 JSON 格式範例"):
        st.code("""
{
  "category": "醫學術語",
  "root_groups": [
    {
      "roots": ["ophthalm-"],
      "meaning": "眼睛",
      "vocabulary": [
        {"word": "Ophthalmology", "breakdown": "ophthalm- + -ology", "definition": "眼科學"}
      ]
    }
  ]
}
        """, language="json")
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
def ui_medical_page(med_data):
    st.title("🏥 醫學術語專業區")
    st.markdown("醫學單字是由精確的**構詞元件**組成的，掌握字根即可推導出複雜術語。")
    
    # 建立側邊欄過濾或上方索引
    all_med_roots = []
    for cat in med_data:
        for group in cat['root_groups']:
            all_med_roots.append(f"{' / '.join(group['roots'])} → {group['meaning']}")
    
    selected_med = st.selectbox("快速定位醫學字根", all_med_roots)
    
    st.divider()
    
    # 顯示內容
    for cat in med_data:
        for group in cat['root_groups']:
            # 如果符合選取的字根則展開，否則預設折疊
            label = f"{' / '.join(group['roots'])} → {group['meaning']}"
            is_expanded = (label == selected_med)
            
            with st.expander(f"🧬 核心字根：{label}", expanded=is_expanded):
                cols = st.columns(2)
                for i, v in enumerate(group['vocabulary']):
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div style="padding:15px; border-radius:10px; border-left:5px solid #ff4b4b; background-color:#f0f2f6; margin-bottom:10px;">
                            <h4 style="margin:0; color:#1f77b4;">{v['word']}</h4>
                            <p style="margin:5px 0; font-size:0.9rem;"><b>拆解：</b><code>{v['breakdown']}</code></p>
                            <p style="margin:0; font-weight:bold;">釋義：{v['definition']}</p>
                        </div>
                        """, unsafe_allow_html=True)
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
            if 'flash_q' in st.session_state: del st.session_state.flash_q
            st.rerun()
        return

    # 2. 練習模式：頂部工具欄
    st.title("記憶卡片")
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.caption(f"目前範圍: {st.session_state.selected_quiz_cat}")
    if col_t2.button("結束", use_container_width=True):
        st.session_state.quiz_active = False
        if 'flash_q' in st.session_state: del st.session_state.flash_q
        st.rerun()

    # 3. 準備題目池
    if st.session_state.selected_quiz_cat == "全部隨機":
        relevant_data = data
    else:
        relevant_data = [c for c in data if c['category'] == st.session_state.selected_quiz_cat]

    all_words = [{**v, "cat": cat['category']} for cat in relevant_data 
                 for group in cat.get('root_groups', []) 
                 for v in group.get('vocabulary', [])]

    if not all_words:
        st.warning("查無單字。")
        if st.button("返回"):
            st.session_state.quiz_active = False
            st.rerun()
        return

    # 4. 智慧抽題邏輯
    if 'flash_q' not in st.session_state:
        st.session_state.is_review = False
        if st.session_state.failed_words and random.random() > 0.5:
            failed_pool = [w for w in all_words if w['word'] in st.session_state.failed_words]
            if failed_pool:
                st.session_state.flash_q = random.choice(failed_pool)
                st.session_state.is_review = True
            else:
                st.session_state.flash_q = random.choice(all_words)
        else:
            st.session_state.flash_q = random.choice(all_words)
        st.session_state.is_flipped = False

    q = st.session_state.flash_q
    is_review = st.session_state.get('is_review', False)
    is_flipped_class = "flipped" if st.session_state.is_flipped else ""

    # 建立複習標籤
    review_tag = '<span style="background-color:#ffeef0;color:#d73a49;padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:bold;margin-left:10px;border:1px solid #f9c2c7;">複習</span>' if is_review else ""

    # 5. 卡片渲染
    card_html = f"""
    <style>
    .flip-card {{ background-color: transparent; width: 100%; height: 350px; perspective: 1000px; }}
    .flip-card-inner {{ position: relative; width: 100%; height: 100%; transition: transform 0.6s; transform-style: preserve-3d; }}
    .flipped {{ transform: rotateY(180deg); }}
    .flip-card-front, .flip-card-back {{ 
        position: absolute; width: 100%; height: 100%; backface-visibility: hidden; 
        border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; 
        background: white; border: 1px solid #e1e4e8; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}
    .flip-card-back {{ transform: rotateY(180deg); padding: 40px; }}
    </style>
    <div class="flip-card">
        <div class="flip-card-inner {is_flipped_class}">
            <div class="flip-card-front">
                <div style="display:flex; align-items:center; justify-content:center;">
                    <small style="color:#888;">{q['cat'].upper()}</small>{review_tag}
                </div>
                <h1 style="font-size:3.2rem; font-weight:700; margin:15px 0; color:#1a1a1a;">{q['word']}</h1>
                <div style="font-size:0.7rem; color:#ccc;">等待翻轉...</div>
            </div>
            <div class="flip-card-back">
                <div style="text-align:left; width:100%;">
                    <div style="font-size:0.8rem; color:#888;">STRUCTURE</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#0366d6; margin-bottom:20px;">{q['breakdown']}</div>
                    <div style="font-size:0.8rem; color:#888;">MEANING</div>
                    <div style="font-size:1.4rem; font-weight:700; color:#24292e;">{q['definition']}</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # 6. 控制按鈕 (整合翻回功能)
    st.write("")
    if not st.session_state.is_flipped:
        if st.button("查看答案", use_container_width=True):
            st.session_state.is_flipped = True
            st.rerun()
    else:
        # 當卡片翻開時，顯示三個功能按鈕
        c1, c2, c3 = st.columns([1, 1, 1])
        
        if c1.button("標記陌生", use_container_width=True):
            st.session_state.failed_words.add(q['word'])
            if 'flash_q' in st.session_state: del st.session_state.flash_q
            st.rerun()
            
        if c2.button("翻回正面", use_container_width=True):
            st.session_state.is_flipped = False
            st.rerun()
            
        if c3.button("標記熟練", use_container_width=True):
            st.session_state.failed_words.discard(q['word'])
            if 'flash_q' in st.session_state: del st.session_state.flash_q
            st.rerun()
# ==========================================
# 3. 主程序
# ==========================================

def main():
    st.set_page_config(page_title="Etymon", layout="wide")
    data = load_db()
    
    st.sidebar.title("Etymon")
    
    # 導航功能
    menu_options = ["字根導覽", "記憶卡片", "醫學專區", "管理後台"]
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
    # 在 main() 函數中修改導航功能
    
    if choice == "字根導覽":
        ui_search_page(data, selected_cat)
    elif choice == "記憶卡片":
        ui_quiz_page(data)
    elif choice == "醫學專區":
        # 直接過濾出醫學分類
        med_data = [c for c in data if "醫學" in c['category']]
        if med_data:
            ui_medical_page(med_data)
        else:
            st.info("目前資料庫中尚無醫學分類資料。請在 JSON 中新增標籤為 '醫學' 的分類。")
    elif choice == "管理後台":
        ui_admin_page() # 呼叫新功能


if __name__ == "__main__":
    main()
