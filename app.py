import streamlit as st
import yfinance as yf
import finnhub
import google.generativeai as genai  # ←ここを修正
from datetime import datetime, timedelta

# --- 画面の設定 ---
st.set_page_config(page_title="AI投資アナリスト yuyu", layout="centered")
st.title("📈 AI投資診断アプリ by yuyu")

# --- サイドバーで設定 ---
st.sidebar.header("API設定")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")
finnhub_key = st.sidebar.text_input("Finnhub API Key", type="password")

ticker = st.text_input("銘柄コード (例: AAPL, 7203.T)", "AAPL").upper()

if st.button("AI診断を開始"):
    if not gemini_key or not finnhub_key:
        st.error("キーを入力してください。")
    else:
        try:
            with st.spinner("分析中..."):
                # --- ここから修正 ---
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                # --- ここまで ---

                # (yfinanceやfinnhubのデータ取得は今のままでOK)
                stock = yf.Ticker(ticker)
                info = stock.info
                # ... (news取得処理) ...

                prompt = f"銘柄:{ticker}, 株価:${info.get('currentPrice')}, ROE:{info.get('returnOnEquity',0)*100:.2f}%, EPS成長:{info.get('earningsGrowth',0)*100:.2f}%\nニュース:\n{news_list}\n上記から、長期投資の観点で買い増し推奨価格とブログ見出し案を日本語で回答して。"
                
                # --- ここを修正 ---
                response = model.generate_content(prompt)

                st.success(f"{ticker} の診断完了！")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
