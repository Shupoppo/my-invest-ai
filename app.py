import streamlit as st
import yfinance as yf
import finnhub
from google import genai  # ← ここを修正しました
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
        st.error("サイドバーにAPIキーを入力してください。")
    else:
        try:
            with st.spinner("分析中..."):
                # 最新の接続ライブラリを使用
                client = genai.Client(api_key=gemini_key)
                
                # 財務データ取得
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # ニュース取得
                finnhub_client = finnhub.Client(api_key=finnhub_key)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
                news_list = "\n".join([f"- {n['headline']}" for n in news[:3]]) if news else "なし"

                # AI診断用プロンプト
                prompt = f"銘柄:{ticker}, 株価:${info.get('currentPrice')}, ROE:{info.get('returnOnEquity',0)*100:.2f}%, EPS成長:{info.get('earningsGrowth',0)*100:.2f}%\nニュース:\n{news_list}\n上記から、長期投資の観点で買い増し推奨価格とブログ見出し案を日本語で回答して。"
                
                # AI診断実行
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )

                # 結果表示
                st.success(f"{ticker} の診断完了！")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
