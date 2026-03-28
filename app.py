import streamlit as st
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# アプリの基本設定
st.set_page_config(page_title="AI投資アナリスト yuyu", layout="wide")
st.title("📈 AI投資診断アプリ by yuyu")
st.caption("世界最新のAIモデルによる銘柄分析（ROE・EPS・最新ニュース重視）")

# --- 1. セキュリティ設定（Secretsから読み込み） ---
# 公開時はStreamlit Cloudの管理画面で設定します
try:
    gemini_key = st.secrets["AIzaSyDilfS86s6m0lelSt1a0tczn22-oHRbZHw"]
    finnhub_key = st.secrets["d73squhr01qno4pvjll0d73squhr01qno4pvjllg"]
    genai.configure(api_key=gemini_key)
except:
    st.error("システム設定エラー：APIキーが見つかりません。")
    st.stop()

# --- 2. ユーザー入力 ---
ticker = st.text_input("分析したい銘柄コードを入力してください (例: AAPL, NVDA, 7203.T)", "NVDA").upper()

if st.button("AIフル分析を実行"):
    try:
        with st.spinner(f"最新モデルで {ticker} を多角的に分析中..."):
            # モデル名は、yuyuさんのリストにあった最新版を指定
            model = genai.GenerativeModel("gemini-3-flash-preview") 
            
            # データ取得
            stock = yf.Ticker(ticker)
            info = stock.info
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
            news_list = "\n".join([f"- {n['headline']}" for n in news[:5]]) if news else "直近の重要ニュースなし"

            # プロンプト（yuyuさんのこだわりを凝縮）
            prompt = (
                f"あなたはプロの投資家『yuyu』として、ブログやYouTubeの視聴者に語りかけるように回答してください。\n\n"
                f"【分析データ】\n"
                f"銘柄: {ticker}\n"
                f"現在価格: ${info.get('currentPrice', '不明')}\n"
                f"ROE: {info.get('returnOnEquity', 0)*100:.2f}%\n"
                f"EPS成長率: {info.get('earningsGrowth', 0)*100:.2f}%\n"
                f"PER: {info.get('forwardPE', '不明')}\n"
                f"ニュース概要: {news_list}\n\n"
                f"【依頼】\n"
                f"1. ROEとEPSの推移から見た企業の「稼ぐ力」の評価\n"
                f"2. ニュースを踏まえた短期的・長期的な展望\n"
                f"3. yuyu流の『買い増し推奨価格』の提示（何ドルまでなら割安か）\n"
                f"4. ブログやSNSで目を引くキャッチコピー案\n"
                f"以上を、親しみやすくも鋭い視点で日本語で解説してください。"
            )
            
            response = model.generate_content(prompt)

            # 結果表示
            st.success("分析が完了しました！")
            st.markdown("---")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"分析中にエラーが発生しました。銘柄コードが正しいか確認してください。")

st.markdown("---")
st.info("※この分析はAIによる予測であり、投資の最終決定はご自身の判断で行ってください。")
