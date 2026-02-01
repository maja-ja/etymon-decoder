import streamlit as st
import pandas as pd

# ==========================================
# 1. Core UI Configuration (English Aesthetic)
# ==========================================
st.set_page_config(page_title="Physics Decoder", page_icon="⚛️", layout="wide")

def inject_physics_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
            
            .physics-breakdown {
                font-family: 'Fira Code', monospace;
                font-size: 2.5rem !important;
                background: linear-gradient(135deg, #FF6F00 0%, #E65100 100%);
                color: #FFFFFF;
                padding: 20px 40px;
                border-radius: 20px;
                display: inline-block;
                margin: 20px 0;
                box-shadow: 0 10px 30px rgba(230, 81, 0, 0.3);
                letter-spacing: 2px;
            }
            .operator { color: #FFE0B2; margin: 0 15px; font-weight: bold; }
            .hero-title { font-size: 5rem; font-weight: 900; color: #E65100; line-height: 1; }
            .unit-sub { font-size: 1.5rem; color: #666; margin-top: 10px; }
            .dimension-tag { 
                background: #FFF3E0; color: #E65100; 
                padding: 6px 18px; border-radius: 50px; font-weight: bold;
                border: 1px solid #FFE0B2; font-family: 'Fira Code', monospace;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. Data Loading (Google Sheet Sync)
# ==========================================
@st.cache_data(ttl=30)
def load_physics_db():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1LeI3C5iHf7_bVEdGG2PaB3WPpbveyYOT3E3OBrY0TWg/export?format=csv"
    try:
        df = pd.read_csv(SHEET_URL)
        return df.fillna("")
    except:
        st.error("Connection Error: Please check Google Sheet permissions.")
        return pd.DataFrame()

# ==========================================
# 3. NMO Rendering Engine (English)
# ==========================================
def render_physics_card(row, o_layer):
    # Header Section
    st.markdown(f"<div class='hero-title'>{row.get('word', 'Unknown')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='unit-sub'>Standard Unit: {row.get('phonetic', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown(f"<span class='dimension-tag'>GENO-CODE: {row.get('roots', 'N/A')}</span>", unsafe_allow_html=True)
    
    # Breakdown Section
    breakdown_text = str(row.get('breakdown', ''))
    styled_breakdown = breakdown_text.replace("*", "<span class='operator'>×</span>").replace("/", "<span class='operator'>÷</span>")
    st.markdown(f"<div class='physics-breakdown'>{styled_breakdown}</div>", unsafe_allow_html=True)

    st.divider()

    # O-Axis Multi-Layer Logic
    if o_layer == 1:
        st.info(f"🧬 **[GENETIC DIMENSION]**\n\nBase Tensor Composition: `{row.get('roots', '')}`\n\nThis code represents the fundamental 'DNA' of the physical quantity across SI dimensions.")
    elif o_layer == 2:
        st.success(f"📚 **[PHYSICS DEFINITION]**\n\n**Definition:** {row.get('definition', '')}\n\n**Common Formula:** `{row.get('example', '')}`")
    else:
        st.warning(f"🌊 **[SENSORY VIBE]**\n\n**Intuition:** {row.get('vibe', '')}\n\n**Memory Hook:** {row.get('memory_hook', '')}")

# ==========================================
# 4. Main Application Flow
# ==========================================
def main():
    inject_physics_css()
    df = load_physics_db()

    # Sidebar UI
    st.sidebar.title("⚛️ Physics Decoder")
    st.sidebar.subheader("Observation Layer (o-axis)")
    o_layer = st.sidebar.select_slider(
        "Slide to switch depth:",
        options=[1, 2, 3],
        format_func=lambda x: {1: "Genetic", 2: "Logic", 3: "Sensory"}[x]
    )

    st.sidebar.markdown("---")
    search = st.sidebar.text_input("🔍 Search Quantity (e.g., Force)")

    # Main Screen Logic
    if search:
        mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
        res = df[mask]
        if not res.empty:
            render_physics_card(res.iloc[0], o_layer)
        else:
            st.error("No results found. Please check your spelling.")
    else:
        if st.button("🎲 Random Discovery"):
            if not df.empty:
                st.session_state.p_data = df.sample(1).iloc[0].to_dict()
                st.rerun()
            
        if 'p_data' in st.session_state:
            render_physics_card(st.session_state.p_data, o_layer)
        else:
            st.write("👈 Search in the sidebar or hit 'Random Discovery' to start.")

if __name__ == "__main__":
    main()
