import streamlit as st
import yfinance as yf
import finnhub
import google.generativeai as genai  # 旧来の安定したライブラリ形式に変更
from datetime import datetime, timedelta

# アプリの基本設定
st.set_page_config(page_title="AI投資アナリスト yuyu", layout="centered")
st.title("📈 AI投資診断アプリ by yuyu")

# --- 1. サイドバーでAPIキーを取得（必ず先に定義する） ---
st.sidebar.header("API設定")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")
finnhub_key = st.sidebar.text_input("Finnhub API Key", type="password")

# --- 2. メイン画面の入力 ---
ticker = st.text_input("銘柄コード (例: AAPL, 7203.T)", "AAPL").upper()

# --- 3. 診断ロジック ---
if st.button("AI診断を開始"):
    # キーが入力されているかチェック
    if not gemini_key or not finnhub_key:
        st.error("サイドバーに Gemini API Key と Finnhub API Key を入力してください。")
    else:
        try:
            with st.spinner(f"{ticker} のデータを分析中..."):
                # --- Geminiの設定 (404エラーを回避する安定版の書き方) ---
                genai.configure(api_key=gemini_key)
                # モデル名は「gemini-1.5-flash」が最も安定して動作します
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # --- yfinanceで株価・指標データを取得 ---
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # --- Finnhubで最新ニュースを取得 ---
                finnhub_client = finnhub.Client(api_key=finnhub_key)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
                news_list = "\n".join([f"- {n['headline']}" for n in news[:3]]) if news else "直近の関連ニュースはありません。"

                # --- AIへのプロンプト作成 ---
                # yuyuさんの分析視点（ROE, EPS）を盛り込んでいます
                prompt = (
                    f"あなたはプロの投資アナリスト『yuyu』として回答してください。\n\n"
                    f"【銘柄情報】\n"
                    f"銘柄名: {ticker}\n"
                    f"現在株価: ${info.get('currentPrice', '取得不可')}\n"
                    f"ROE: {info.get('returnOnEquity', 0)*100:.2f}%\n"
                    f"EPS成長率: {info.get('earningsGrowth', 0)*100:.2f}%\n\n"
                    f"【最新ニュース】\n"
                    f"{news_list}\n\n"
                    f"上記データに基づき、長期投資の観点から「いくらまでなら割安と言えるか（買い増し推奨価格）」と、"
                    f"投資ブログ・YouTubeで使える「キャッチーな見出し案」を日本語で詳しく回答してください。"
                )
                
                # --- AIによる生成実行 ---
                response = model.generate_content(prompt)

                # --- 結果の表示 ---
                st.success(f"{ticker} の診断が完了しました！")
                st.markdown("---")
                st.markdown(response.text)
                
        except Exception as e:
            # 万が一エラーが出た場合、内容を表示する
            st.error(f"診断中にエラーが発生しました: {e}")

# フッター
st.caption("© 2026 AI投資アナリスト yuyu - 投資は自己責任でお願いします。")
