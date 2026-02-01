import streamlit as st
from streamlit_elements import elements, mui, dashboard
import pandas as pd

# ==========================================
# 1. 初始化與樣式
# ==========================================
st.set_page_config(page_title="Physics Decoder: Lab", page_icon="⚛️", layout="wide")

def load_db():
    # 這裡維持讀取你的 Google Sheet
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL).fillna("")
    except:
        return pd.DataFrame({'word':['Force'], 'breakdown':['m * a'], 'category':['Mechanics'], 'definition':['Push or pull']})

# ==========================================
# 2. 側邊欄控制
# ==========================================
st.sidebar.title("⚛️ Physics Lab")
df = load_db()
selected_word = st.sidebar.selectbox("選擇物理量", df['word'].tolist())
row = df[df['word'] == selected_word].iloc[0]

# 解析拆解塊 (例如: "m * a" -> ["m", "a"])
parts = str(row['breakdown']).replace("*", "|").replace("/", "|").split("|")
parts = [p.strip() for p in parts]

st.sidebar.info("💡 提示：在右側工作區可以自由拖拉、縮放這些方塊！")

# ==========================================
# 3. 拖拉式儀表板實作 (Streamlit Elements)
# ==========================================
# 這裡我們使用 streamlit_elements 庫來達成拖拉效果
# 如果環境中沒安裝，請執行: pip install streamlit-elements
from streamlit_elements import elements, mui, dashboard

with elements("physics_dashboard"):
    
    # 定義佈局：每個方塊的 ID, x坐標, y坐標, 寬, 高
    layout = [
        # 主物理量方塊
        dashboard.Item("main", 0, 0, 4, 2),
        # 公式拆解方塊 (動態生成)
    ]
    
    # 動態為每個拆解零件增加佈局
    for i, p in enumerate(parts):
        layout.append(dashboard.Item(f"part_{i}", (i*2)%12, 2, 2, 1))
        
    # 定義卡片樣式
    card_style = {
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "alignItems": "center",
        "borderRadius": "12px",
        "boxShadow": "0 4px 20px rgba(0,0,0,0.1)",
        "background": "white",
        "border": "1px solid #e0e0e0"
    }

    with dashboard.Grid(layout):
        # 1. 主物理量卡片
        with mui.Card(key="main", sx={**card_style, "background": "linear-gradient(135deg, #1E88E5 0%, #1565C0 100%)", "color": "white"}):
            mui.Typography(row['word'], variant="h2", sx={"fontWeight": "900"})
            mui.Typography("主物理量", variant="overline")

        # 2. 拆解零件卡片 (可拖拉)
        for i, p in enumerate(parts):
            with mui.Card(key=f"part_{i}", sx=card_style):
                mui.Typography("COMPONENT", variant="caption", sx={"color": "#1E88E5"})
                mui.Typography(p, variant="h4", sx={"fontWeight": "bold"})
                mui.Typography("⚡ 物理因子", variant="body2", sx={"color": "#888"})

        # 3. 定義與語感 (如果需要也可以變方塊)
        with mui.Card(key="desc", sx=0, sy=3, sw=6, sh=2, sx_style=card_style):
            mui.CardContent():
                mui.Typography("🎯 物理定義", gutterBottom=True, variant="h6", component="div")
                mui.Typography(row['definition'], variant="body1")

# ==========================================
# 4. 補充說明
# ==========================================
st.markdown("---")
st.caption("本介面採用物理建模思維，您可以將各個『物理零件』自由排列以觀察其關聯性。")
