import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心 CSS (完全復刻 Etymon Decoder 視覺)
# ==========================================
st.set_page_config(page_title="Physics Decoder", page_icon="⚛️", layout="wide")

def inject_etymon_style():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Noto+Sans+TC:wght@500;900&display=swap');
            
            html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }

            /* 標題與語音感標籤 */
            .main-word { font-size: 5rem; font-weight: 900; color: #1E88E5; margin-bottom: 0px; letter-spacing: -2px; }
            .unit-text { font-size: 1.5rem; color: #666; font-family: 'Fira Code', monospace; margin-bottom: 20px; }

            /* 物理字根拆解塊 (核心視覺) */
            .root-container { display: flex; align-items: center; margin: 30px 0; flex-wrap: wrap; }
            .root-block {
                background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
                color: white; padding: 15px 30px; border-radius: 12px;
                font-size: 1.8rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .root-operator { font-size: 2rem; color: #1E88E5; margin: 0 15px; font-weight: bold; }

            /* 內容資訊卡 */
            .info-card {
                background: #F8F9FA; border-left: 5px solid #1E88E5;
                padding: 20px; border-radius: 8px; margin: 10px 0;
            }
            .section-label { font-weight: bold; color: #1565C0; margin-bottom: 5px; font-size: 0.9rem; }
            
            /* 側邊欄 Era Gateway 風格按鈕 */
            .stButton > button {
                width: 100%; border-radius: 8px; border: 1px solid #ddd;
                background-color: white; transition: 0.3s; font-weight: bold;
            }
            .stButton > button:hover { border-color: #1E88E5; background-color: #E3F2FD; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料讀取
# ==========================================
@st.cache_data(ttl=30)
def load_db():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL).fillna("")
    except:
        return pd.DataFrame({'word':['Error'], 'category':['Error']})

# ==========================================
# 3. 渲染主介面 (拿掉維度分析)
# ==========================================
def render_physics_interface(row, o_layer):
    # 標題
    st.markdown(f"<div class='main-word'>{row['word']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='unit-text'>// 標準單位: {row['phonetic']} //</div>", unsafe_allow_html=True)

    # 物理拆解塊
    breakdown = str(row['breakdown'])
    op = "×" if "*" in breakdown else "÷" if "/" in breakdown else ""
    parts = breakdown.replace("*", "|").replace("/", "|").split("|")
    
    html = "<div class='root-container'>"
    for i, p in enumerate(parts):
        html += f"<div class='root-block'>{p.strip()}</div>"
        if i < len(parts) - 1:
            html += f"<div class='root-operator'>{op}</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # 內容卡片 (根據 o_layer 切換：定義層 vs 語感層)
    col1, col2 = st.columns([1.5, 1])
    with col1:
        if o_layer == 2: # 定義層
            st.markdown(f"""
                <div class='info-card'>
                    <div class='section-label'>🎯 定義</div>{row['definition']}
                </div>
                <div class='info-card'>
                    <div class='section-label'>📖 常用公式</div><code>{row['example']}</code>
                </div>
            """, unsafe_allow_html=True)
        else: # 語感層 (預設與 layer 3)
            st.markdown(f"""
                <div class='info-card'>
                    <div class='section-label'>🌊 語感</div>{row['vibe']}
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='info-card' style='border-left-color: #FFA000;'>
                <div class='section-label'>💡 記憶鉤子</div>{row['memory_hook']}
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程式 (側邊欄分區按鈕)
# ==========================================
def main():
    inject_etymon_style()
    df = load_db()

    # 側邊欄
    st.sidebar.title("⚛️ Physics Decoder")
    
    st.sidebar.write("### 領域分區 (Era Gateway)")
    categories = ["全部"] + list(df['category'].unique())
    
    # 使用按鈕或 selectbox 模擬分區
    selected_cat = st.sidebar.selectbox("選擇領域", categories)
    
    st.sidebar.markdown("---")
    o_layer = st.sidebar.select_slider(
        "觀測深度 (o-axis)",
        options=[2, 3], # 刪除 layer 1 (維度層)
        format_func=lambda x: {2: "定義/公式", 3: "感官語感"}[x]
    )

    # 數據篩選
    filtered_df = df if selected_cat == "全部" else df[df['category'] == selected_cat]

    st.sidebar.markdown("---")
    if st.sidebar.button("下一個物理量 ➜", use_container_width=True):
        st.session_state.current_phys = filtered_df.sample(1).iloc[0].to_dict()

    if 'current_phys' not in st.session_state and not filtered_df.empty:
        st.session_state.current_phys = filtered_df.iloc[0].to_dict()

    if 'current_phys' in st.session_state:
        render_physics_interface(st.session_state.current_phys, o_layer)

if __name__ == "__main__":
    main()
