import streamlit as st
import pandas as pd
import base64
import time
import json
from io import BytesIO
from gtts import gTTS
import streamlit.components.v1 as components

# ==========================================
# 1. 核心配置與 CSS (物理字根專屬優化)
# ==========================================
st.set_page_config(page_title="Physics Decoder v1.0", page_icon="⚛️", layout="wide")

def inject_physics_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Noto+Sans+TC:wght@500;700&display=swap');

            .physics-breakdown {
                font-family: 'Fira Code', monospace;
                font-size: 2rem !important;
                background: linear-gradient(135deg, #FF6F00 0%, #E65100 100%);
                color: #FFFFFF;
                padding: 15px 35px;
                border-radius: 20px;
                display: inline-block;
                margin: 20px 0;
                box-shadow: 0 10px 20px rgba(230, 81, 0, 0.2);
            }
            .operator { color: #FFE0B2; margin: 0 10px; font-weight: bold; }
            .hero-title { font-size: 4rem; font-weight: 900; color: #E65100; }
            .dimension-tag { 
                background: #FFF3E0; 
                color: #E65100; 
                padding: 5px 15px; 
                border-radius: 50px; 
                font-size: 1.2rem;
                border: 1px solid #FFE0B2;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 物理核心邏輯 (n x m x o)
# ==========================================
def n_m_o_physics_engine(row, o_layer):
    """
    將資料庫行數據 映射至 n-m-o 觀測面
    o=1: 基因維度 | o=2: 物理定義 | o=3: 感官語感
    """
    if o_layer == 1:
        return f"🧬 維度密碼 (1-7): \n `{row['roots']}`"
    elif o_layer == 2:
        return f"📚 物理語法: \n {row['definition']}"
    else:
        return f"🌊 直覺語感: \n {row['vibe']}"

# ==========================================
# 3. 資料讀取 (建議欄位：category, roots, meaning, word, breakdown, definition, vibe, example, hook)
# ==========================================
@st.cache_data(ttl=60)
def load_physics_db():
    # 這裡預留你的 Google Sheet ID
    SHEET_ID = "你的_GOOGLE_SHEET_ID" 
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
    
    # 模擬數據（若沒接通 Google Sheet 時使用）
    mock_data = {
        'category': ['力學', '電學', '磁學'],
        'word': ['Force (F)', 'Voltage (V)', 'Magnetic Field (B)'],
        'roots': ['[1,1,-2,0,0,0,0]', '[1,2,-3,-1,0,0,0]', '[1,0,-2,-1,0,0,0]'],
        'breakdown': ['Mass * Accel', 'Energy / Charge', 'Force / (q*v)'],
        'definition': ['改變運動狀態的作用', '單位電荷的能量差', '磁力空間性質'],
        'vibe': ['推動的沉重感', '推動電子流動的壓力', '看不見的旋轉引導力'],
        'example': ['F = ma', 'V = IR', 'F = qvB'],
        'hook': ['牛頓第二定律', '電路的原動力', '右手開掌定則']
    }
    try:
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame(mock_data)

# ==========================================
# 4. 渲染百科全書卡片 (Physics Style)
# ==========================================
def render_physics_card(row, o_val):
    st.markdown(f"<div class='hero-title'>{row['word']}</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dimension-tag'>Dim: {row['roots']}</span>", unsafe_allow_html=True)
    
    # 這裡必須用 st.markdown 並開啟 unsafe_allow_html
    styled_breakdown = str(row['breakdown']).replace("*", "<span class='operator'>×</span>").replace("/", "<span class='operator'>÷</span>")
    st.markdown(f"<div class='physics-breakdown'>{styled_breakdown}</div>", unsafe_allow_html=True)

    # N-M-O 動態層：建議改用不同顏色區分深度
    display_content = n_m_o_physics_engine(row, o_val)
    if o_val == 1:
        st.code(display_content, language="python") # 密碼層用代碼框
    elif o_val == 2:
        st.info(display_content) # 定義層用藍框
    else:
        st.warning(display_content) # 語感層用黃框
# ==========================================
# 5. 主程式
# ==========================================
def main():
    inject_physics_css()
    df = load_physics_db()

    st.sidebar.title("⚛️ Physics Decoder")
    mode = st.sidebar.radio("導航選單", ["張量觀測站 (NMO)", "物理基因庫", "Mix Lab 合成器"])

    if mode == "張量觀測站 (NMO)":
        st.title("Pino 物理建模：n x m x o 觀測站")
        
        # O 軸控制
        o_layer = st.select_slider(
            "切換邏輯觀測深度 (o-axis)",
            options=[1, 2, 3],
            format_func=lambda x: {1: "基因維度", 2: "物理定義", 3: "感官語感"}[x]
        )

        st.divider()

        # 隨機抽一個物理量來展示切片
        if st.button("🎲 觀測下一個物理量"):
            st.session_state.current_phys = df.sample(1).iloc[0].to_dict()

        if 'current_phys' in st.session_state:
            render_physics_card(st.session_state.current_phys, o_layer)

    elif mode == "物理基因庫":
        st.title("物理字根搜尋列表")
        search = st.text_input("🔍 輸入關鍵字或維度向量搜尋...")
        if search:
            mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
            st.dataframe(df[mask], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    elif mode == "Mix Lab 合成器":
        st.title("Mix Lab: 物理公式合成實驗室")
        st.write("這是在 14 欄位邏輯下，透過「維度加減」預測新物理量的功能（開發中）。")
        # 這裡可以嵌入你之前寫的 React Wheel 組件

if __name__ == "__main__":
    main()
