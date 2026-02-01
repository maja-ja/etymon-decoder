import streamlit as st
import pandas as pd

# ==========================================
# 1. 核心 CSS (包含側邊欄按鈕優化)
# ==========================================
st.set_page_config(page_title="Physics Decoder v2.5", page_icon="⚛️", layout="wide")

def inject_physics_style():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Noto+Sans+TC:wght@500;900&display=swap');
            
            /* 全域設定 */
            html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }

            /* 側邊欄 Era Gateway 按鈕風格 */
            .stSidebar [data-testid="stVerticalBlock"] > div:nth-child(1) {
                background-color: #f0f2f6;
                padding: 10px;
                border-radius: 10px;
            }
            
            /* 模擬 Era Gateway 分區按鈕樣式 */
            .section-btn {
                width: 100%;
                padding: 10px;
                margin: 5px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
                text-align: center;
                cursor: pointer;
                font-weight: bold;
                transition: 0.3s;
            }
            .section-btn:hover { background: #E3F2FD; border-color: #1E88E5; }

            /* 主畫面內容樣式 (復刻 Etymon) */
            .main-word { font-size: 5rem; font-weight: 900; color: #1E88E5; margin-bottom: 0px; letter-spacing: -2px; }
            .phonetic { font-size: 1.5rem; color: #666; font-family: 'Fira Code', monospace; margin-bottom: 20px; }
            .dim-pill { 
                background: #E3F2FD; color: #1565C0; padding: 4px 15px; border-radius: 50px; 
                font-size: 0.9rem; font-weight: bold; border: 1px solid #BBDEFB;
            }

            /* 物理塊 (Roots) */
            .root-container { display: flex; align-items: center; margin: 30px 0; flex-wrap: wrap; }
            .root-block {
                background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
                color: white; padding: 15px 25px; border-radius: 12px;
                font-size: 1.8rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .root-operator { font-size: 2rem; color: #1E88E5; margin: 0 15px; font-weight: bold; }

            /* 卡片風格 */
            .info-card {
                background: #F8F9FA; border-left: 5px solid #1E88E5;
                padding: 20px; border-radius: 8px; margin: 10px 0;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料處理
# ==========================================
@st.cache_data(ttl=30)
def load_db():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/export?format=csv"
    try:
        df = pd.read_csv(SHEET_URL)
        return df.fillna("")
    except:
        return pd.DataFrame({'word':['Error'], 'roots':['N/A'], 'category':['Error']})

# ==========================================
# 3. 側邊欄：分區按鈕設計 (Era Gateway 復刻)
# ==========================================
def render_sidebar(df):
    st.sidebar.title("⚛️ Physics Decoder")
    
    st.sidebar.subheader("領域分區")
    # 這裡模擬 Era Gateway 的按鈕群組
    categories = ["全部"] + list(df['category'].unique())
    
    # 使用 st.radio 並隱藏原始樣式，或者直接用 selectbox (Streamlit 限制，按鈕觸發較難保持狀態)
    # 為了穩定性，我們使用 selectbox 並優化視覺感，或者使用 Button 觸發
    selected_cat = st.sidebar.selectbox("選擇物理領域", categories)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("觀測深度 (o-axis)")
    o_layer = st.sidebar.select_slider(
        "切換維度",
        options=[1, 2, 3],
        format_func=lambda x: {1:"基因碼", 2:"定義層", 3:"語感層"}[x]
    )
    
    st.sidebar.markdown("---")
    search = st.sidebar.text_input("🔍 搜尋物理量")
    
    return selected_cat, o_layer, search

# ==========================================
# 4. 主畫面渲染
# ==========================================
def render_content(row, o_layer):
    st.markdown(f"<div class='main-word'>{row['word']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='phonetic'>// {row['phonetic']} //</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dim-pill'>🧬 基因碼: {row['roots']}</span>", unsafe_allow_html=True)

    # 拆解區
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

    # 卡片內容
    c1, c2 = st.columns([2, 1])
    with c1:
        if o_layer == 1:
            st.markdown(f"<div class='info-card'><b>維度分析：</b><br>{row['roots']}</div>", unsafe_allow_html=True)
        elif o_layer == 2:
            st.markdown(f"<div class='info-card'><b>核心定義：</b><br>{row['definition']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='info-card'><b>公式：</b><br><code>{row['example']}</code></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='info-card'><b>感官語感：</b><br>{row['vibe']}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='info-card' style='border-left-color:orange;'><b>記憶鉤子：</b><br>{row['memory_hook']}</div>", unsafe_allow_html=True)

# ==========================================
# 5. 執行
# ==========================================
def main():
    inject_physics_style()
    df = load_db()
    
    cat, o, search = render_sidebar(df)
    
    # 篩選數據
    filtered_df = df if cat == "全部" else df[df['category'] == cat]
    
    if search:
        filtered_df = filtered_df[filtered_df['word'].str.contains(search, case=False)]

    if st.sidebar.button("下一個物理量 ➜", use_container_width=True):
        if not filtered_df.empty:
            st.session_state.current = filtered_df.sample(1).iloc[0].to_dict()

    if 'current' not in st.session_state and not filtered_df.empty:
        st.session_state.current = filtered_df.iloc[0].to_dict()

    if 'current' in st.session_state:
        render_content(st.session_state.current, o)

if __name__ == "__main__":
    main()
