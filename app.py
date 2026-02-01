import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心視覺配置 (修正 HTML 標籤渲染問題)
# ==========================================
st.set_page_config(page_title="Physics Decoder", page_icon="⚛️", layout="wide")

def inject_physics_css():
    st.markdown("""
        <style>
            .physics-breakdown {
                font-family: 'Courier New', monospace;
                font-size: 2.2rem !important;
                background: linear-gradient(135deg, #FF6F00 0%, #E65100 100%);
                color: #FFFFFF;
                padding: 15px 35px;
                border-radius: 15px;
                display: inline-block;
                margin: 15px 0;
                box-shadow: 0 4px 15px rgba(230, 81, 0, 0.3);
            }
            .operator { color: #FFE0B2; margin: 0 10px; font-weight: bold; }
            .hero-title { font-size: 4.5rem; font-weight: 900; color: #E65100; margin-bottom: -10px; }
            .dimension-tag { 
                background: #FFF3E0; color: #E65100; 
                padding: 4px 12px; border-radius: 50px; font-weight: bold;
                border: 1px solid #FFE0B2;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料讀取邏輯 (對齊你的 Google Sheet 欄位)
# ==========================================
@st.cache_data(ttl=30)
def load_physics_db():
    # 請替換為你的 Google Sheet CSV 連結
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/export?format=csv"
    try:
        df = pd.read_csv(SHEET_URL)
        return df.fillna("")
    except:
        # 僅在讀取失敗時顯示的開發測試數據
        return pd.DataFrame({
            'word': ['Force (F)'],
            'roots': ['[1, 1, -2, 0, 0, 0, 0]'],
            'breakdown': ['Mass * Accel'],
            'definition': ['改變物體運動狀態的作用'],
            'phonetic': ['Newton'],
            'example': ['F = ma'],
            'vibe': ['推動重物時的肌肉緊繃感'],
            'memory_hook': ['牛頓第二定律的核心']
        })

# ==========================================
# 3. NMO 渲染引擎 (o-axis)
# ==========================================
def render_physics_card(row, o_layer):
    # 標題區
    st.markdown(f"<div class='hero-title'>{row.get('word', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: #666; font-size: 1.2rem; margin-bottom: 8px;'>單位：{row.get('phonetic', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dimension-tag'>基因碼: {row.get('roots', 'N/A')}</span>", unsafe_allow_html=True)
    
    # 結構拆解 (核心：使用 markdown 配合 HTML 渲染標籤)
    breakdown_text = str(row.get('breakdown', ''))
    styled_breakdown = breakdown_text.replace("*", "<span class='operator'>×</span>").replace("/", "<span class='operator'>÷</span>")
    st.markdown(f"<div class='physics-breakdown'>{styled_breakdown}</div>", unsafe_allow_html=True)

    st.divider()

    # O-Axis 分層邏輯
    if o_layer == 1:
        st.info(f"🧬 **[基因維度層]**\n\n底層維度組成：`{row.get('roots', '')}`\n\n這反映了該物理量在宇宙基本度量（M, L, T...）中的位置。")
    elif o_layer == 2:
        st.success(f"📚 **[物理定義層]**\n\n**定義：** {row.get('definition', '')}\n\n**標準公式：** `{row.get('example', '')}`")
    else:
        st.warning(f"🌊 **[感官語感層]**\n\n**直覺語感：** {row.get('vibe', '')}\n\n**記憶點：** {row.get('memory_hook', '')}")

# ==========================================
# 4. 主程式流程
# ==========================================
def main():
    inject_physics_css()
    df = load_physics_db()

    # 側邊欄控制
    st.sidebar.title("⚛️ P 物理建模")
    o_layer = st.sidebar.select_slider(
        "切換觀測深度 (o-axis)",
        options=[1, 2, 3],
        format_func=lambda x: {1: "基因碼", 2: "定義層", 3: "語感層"}[x]
    )

    st.sidebar.markdown("---")
    search = st.sidebar.text_input("🔍 搜尋物理量 (例如: Force)")

    # 主畫面邏輯
    if search:
        # 模糊搜尋
        mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
        res = df[mask]
        if not res.empty:
            render_physics_card(res.iloc[0], o_layer)
        else:
            st.error("查無此物理量，請檢查拼字。")
    else:
        # 預設隨機探索模式
        if st.button("🎲 隨機觀測下一物理量"):
            st.session_state.p_data = df.sample(1).iloc[0].to_dict()
            st.rerun()
            
        if 'p_data' in st.session_state:
            render_physics_card(st.session_state.p_data, o_layer)
        else:
            st.write("👈 請從左側搜尋，或點擊隨機觀測。")

if __name__ == "__main__":
    main()
