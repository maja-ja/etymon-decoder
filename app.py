import streamlit as st
import pandas as pd

# ==========================================
# 1. Etymon 風格 CSS 注入
# ==========================================
st.set_page_config(page_title="Physics Decoder v2.5", page_icon="⚛️", layout="wide")

def inject_etymon_style():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Noto+Sans+TC:wght@500;900&display=swap');
            
            /* 全域字體設定 */
            html, body, [class*="css"] {
                font-family: 'Noto Sans TC', sans-serif;
            }

            /* 標題與標籤 */
            .main-word { font-size: 5rem; font-weight: 900; color: #1E88E5; margin-bottom: 0px; letter-spacing: -2px; }
            .phonetic { font-size: 1.5rem; color: #666; font-family: 'Fira Code', monospace; margin-bottom: 20px; }
            .dim-pill { 
                background: #E3F2FD; color: #1565C0; padding: 4px 15px; border-radius: 50px; 
                font-size: 0.9rem; font-weight: bold; border: 1px solid #BBDEFB;
            }

            /* 字根拆解塊 (最重要介面) */
            .root-container { display: flex; align-items: center; margin: 30px 0; }
            .root-block {
                background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
                color: white; padding: 15px 30px; border-radius: 12px;
                font-size: 1.8rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .root-operator { font-size: 2rem; color: #1E88E5; margin: 0 15px; font-weight: bold; }

            /* 內容卡片 */
            .info-card {
                background: #F8F9FA; border-left: 5px solid #1E88E5;
                padding: 20px; border-radius: 8px; margin: 10px 0;
            }
            .section-header { font-weight: bold; color: #1565C0; margin-bottom: 10px; display: flex; align-items: center; }
            
            /* 漸層按鈕自定義 */
            .stButton>button {
                background: linear-gradient(to right, #FF4B2B, #FF416C);
                color: white; border: none; padding: 10px 25px; border-radius: 50px;
                font-weight: bold; transition: 0.3s;
            }
            .stButton>button:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(255, 75, 43, 0.4); }
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
        return pd.DataFrame({'word':['Error'], 'roots':['N/A']})

# ==========================================
# 3. 介面渲染函數 (復刻版)
# ==========================================
def render_physics_interface(row, o_layer):
    # 標題與單位
    st.markdown(f"<div class='main-word'>{row.get('word', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='phonetic'>// {row.get('phonetic', 'N/A')} //</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dim-pill'>🧬 基因碼: {row.get('roots', 'N/A')}</span>", unsafe_allow_html=True)

    # 字根拆解區 (Breakdown)
    # 將 "Mass * Accel" 轉換為 UI 塊
    raw_breakdown = str(row.get('breakdown', ''))
    if "*" in raw_breakdown:
        parts = raw_breakdown.split("*")
        op = "×"
    elif "/" in raw_breakdown:
        parts = raw_breakdown.split("/")
        op = "÷"
    else:
        parts = [raw_breakdown]
        op = ""

    breakdown_html = "<div class='root-container'>"
    for i, p in enumerate(parts):
        breakdown_html += f"<div class='root-block'>{p.strip()}</div>"
        if i < len(parts) - 1:
            breakdown_html += f"<div class='root-operator'>{op}</div>"
    breakdown_html += "</div>"
    st.markdown(breakdown_html, unsafe_allow_html=True)

    # 深度內容區 (依據 o-axis)
    col1, col2 = st.columns([1.5, 1])

    with col1:
        if o_layer == 1:
            st.markdown(f"""
                <div class='info-card'>
                    <div class='section-header'>🧬 維度解碼 (Dimension)</div>
                    此物理量的宇宙組成代碼為 <b>{row.get('roots')}</b>。<br>
                    這代表了它在質量 (M)、長度 (L)、時間 (T) 之間的比例關係。
                </div>
            """, unsafe_allow_html=True)
        elif o_layer == 2:
            st.markdown(f"""
                <div class='info-card'>
                    <div class='section-header'>🎯 核心定義 (Definition)</div>
                    {row.get('definition', '尚未輸入定義')}
                </div>
                <div class='info-card'>
                    <div class='section-header'>📝 實戰公式 (Example)</div>
                    <code>{row.get('example', 'N/A')}</code>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='info-card'>
                    <div class='section-header'>🌊 直覺感官 (Vibe)</div>
                    {row.get('vibe', '尚未輸入感官描述')}
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='info-card' style='border-left-color: #FFA000;'>
                <div class='section-header'>💡 記憶鉤子</div>
                {row.get('memory_hook', '無')}
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. 主程式
# ==========================================
def main():
    inject_etymon_style()
    df = load_db()

    # 側邊欄導航
    st.sidebar.title("⚛️ Physics Decoder")
    
    # 模仿 Era Gateway 的分類篩選
    category = st.sidebar.selectbox("分類篩選", ["全部"] + list(df['category'].unique()))
    
    o_layer = st.sidebar.select_slider(
        "觀測深度 (o-axis)",
        options=[1, 2, 3],
        format_func=lambda x: {1:"基因維度", 2:"定義/公式", 3:"感官記憶"}[x]
    )

    if category != "全部":
        filtered_df = df[df['category'] == category]
    else:
        filtered_df = df

    # 主畫面邏輯
    st.sidebar.markdown("---")
    if st.sidebar.button("下一個物理量 ➜"):
        st.session_state.current_data = filtered_df.sample(1).iloc[0].to_dict()

    if 'current_data' not in st.session_state and not filtered_df.empty:
        st.session_state.current_data = filtered_df.iloc[0].to_dict()

    if 'current_data' in st.session_state:
        render_physics_interface(st.session_state.current_data, o_layer)

if __name__ == "__main__":
    main()
