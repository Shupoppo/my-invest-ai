import streamlit as st
import yfinance as yf
import finnhub
from google import genai
from datetime import datetime, timedelta

st.set_page_config(page_title="AI投資アナリスト yuyu", layout="centered")
st.title("📈 AI投資診断アプリ by yuyu")

# サイドバーに「今使えるモデル一覧」を出すデバッグ用
if st.sidebar.button("利用可能なモデルをリストアップ"):
    temp_client = genai.Client(api_key=gemini_key)
    for m in temp_client.models.list():
        st.sidebar.code(m.name)

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
                # 接続の強制リセット
                client = genai.Client(api_key=gemini_key)
                
                stock = yf.Ticker(ticker)
                info = stock.info
                
                finnhub_client = finnhub.Client(api_key=finnhub_key)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
                news_list = "\n".join([f"- {n['headline']}" for n in news[:3]]) if news else "なし"

                prompt = f"銘柄:{ticker}, 株価:${info.get('currentPrice')}, ROE:{info.get('returnOnEquity',0)*100:.2f}%, EPS成長:{info.get('earningsGrowth',0)*100:.2f}%\nニュース:\n{news_list}\n上記から、長期投資の観点で買い増し推奨価格とブログ見出し案を日本語で回答して。"
                
                # 最も安定した呼び出し
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )

                st.success(f"{ticker} の診断完了！")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
