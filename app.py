import streamlit as st
import google.generativeai as genai

# 配置你的 Gemini API
genai.configure(api_key="你的_GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🚀 詞源解構生成器")

# 1. 輸入詞根
root_input = st.text_input("輸入詞根 (Root)，例如: spect, ject, tract", placeholder="spect")

if root_input:
    if st.button(f"執行衍生導出: -{root_input}-"):
        with st.spinner('正在分析詞源結構...'):
            # 2. 構造 Prompt，要求 AI 回傳結構化資料
            prompt = f"""
            你是一個專業的英語詞源學家。請針對詞根 "{root_input}"，
            導出 5 個常見的 [Prefix]-[Root]-[Suffix] 組合。
            請嚴格遵守以下格式回傳，不要有額外文字：
            單字 | 結構拆解 | 核心語義
            """
            
            response = model.generate_content(prompt)
            
            # 3. 渲染結果
            st.markdown(f"### 找到關於 `{root_input}` 的衍生族譜：")
            st.write(response.text)
