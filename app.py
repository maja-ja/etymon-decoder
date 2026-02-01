import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心 CSS (精簡 UI，確保 HTML 渲染)
# ==========================================
st.set_page_config(page_title="Physics Decoder", page_icon="⚛️", layout="wide")

def inject_physics_css():
    st.markdown("""
        <style>
            .physics-breakdown {
                font-family: monospace;
                font-size: 2.2rem !important;
                background: linear-gradient(135deg, #FF6F00 0%, #E65100 100%);
                color: #FFFFFF;
                padding: 15px 35px;
                border-radius: 15px;
                display: inline-block;
                margin: 15px 0;
            }
            .operator { color: #FFE0B2; margin: 0 10px; font-weight: bold; }
            .hero-title { font-size: 4.5rem; font-weight: 900; color: #E65100; margin-bottom: -10px; }
            .dimension-tag { 
                background: #FFF3E0; color: #E65100; 
                padding: 4px 12px; border-radius: 50px; font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料讀取 (僅保留雲端連結邏輯)
# ==========================================
@st.cache_data(ttl=60)
def load_physics_db():
    # 填入你的 Google Sheet CSV 連結
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/edit?gid=0#gid=0"
    try:
        return pd.read_csv(SHEET_URL).fillna("")
    except:
        st.error("❌ 無法讀取資料庫，請檢查 Google Sheet 權限或連結。")
        return pd.DataFrame()

# ==========================================
# 3. 渲染邏輯 (o-axis 切片)
# ==========================================
def render_physics_card(row, o_layer):
    # 1. 抓取資料（使用 get 預防 Key 錯誤）
    word = row.get('word', 'Unknown')
    roots = row.get('roots', '[0,0,0,0,0,0,0]')
    unit = row.get('phonetic', '')  # 在物理版中，phonetic 欄位拿來放單位 (如 Newton)
    breakdown = row.get('breakdown', '')
    definition = row.get('definition', '')
    example = row.get('example', '')
    vibe = row.get('vibe', '')
    hook = row.get('memory_hook', row.get('hook', '')) # 兼容兩個可能的欄位名

    # 2. 標題與單位渲染
    st.markdown(f"<div class='hero-title'>{word}</div>", unsafe_allow_html=True)
    if unit:
        st.markdown(f"<div style='font-size: 1.5rem; color: #666; margin-bottom: 10px;'>標準單位: {unit}</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dimension-tag'>基因碼: {roots}</span>", unsafe_allow_html=True)
    
    # 3. 結構拆解渲染
    styled_breakdown = str(breakdown).replace("*", "<span class='operator'>×</span>").replace("/", "<span class='operator'>÷</span>")
    st.markdown(f"<div class='physics-breakdown'>{styled_breakdown}</div>", unsafe_allow_html=True)

    # 4. N-M-O 觀測深度切換
    st.divider()
    if o_layer == 1:
        st.info(f"🧬 **[基因維度層]**\n\n底層代碼：`{roots}`\n\n這代表了該量在質量、長度、時間等 7 個基本維度的組成。")
    elif o_layer == 2:
        st.success(f"📚 **[物理定義層]**\n\n**定義：** {definition}\n\n**常用公式：** `{example}`")
    else:
        st.warning(f"🌊 **[感官語感層]**\n\n**直覺語感：** {vibe}\n\n**記憶鉤子：** {hook}")

# ==========================================
# 4. 主程式 (刪除多餘 Menu，直球對決)
# ==========================================
def main():
    inject_physics_css()
    df = load_physics_db()

    if df.empty: return

    # 側邊欄：僅保留 NMO 控制
    st.sidebar.title("⚛️ Pino 建模")
    o_layer = st.sidebar.select_slider(
        "切換觀測深度 (o-axis)",
        options=[1, 2, 3],
        format_func=lambda x: ["", "基因碼", "定義層", "語感層"][x]
    )
    
    search_query = st.sidebar.text_input("🔍 搜尋物理量 (或輸入維度)")

    # 主畫面
    if search_query:
        mask = df.apply(lambda r: search_query.lower() in str(r.values).lower(), axis=1)
        results = df[mask]
        if not results.empty:
            render_physics_card(results.iloc[0], o_layer)
        else:
            st.write("查無此量，請確認輸入。")
    else:
        if st.button("🎲 隨機觀測下一量"):
            st.session_state.current_phys = df.sample(1).iloc[0].to_dict()
        
        if 'current_phys' in st.session_state:
            render_physics_card(st.session_state.current_phys, o_layer)
        else:
            st.write("請從左側搜尋或點擊隨機觀測。")

if __name__ == "__main__":
    main()
