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
    gemini_key = st.secrets["GEMINI_API_KEY"]
    finnhub_key = st.secrets["FINNHUB_API_KEY"]
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

            # --- AIへのプロンプト作成（キャッチコピー案を削除したVer.） ---
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
    f"1. ROEとEPSの推移から見た企業の「稼ぐ力」を、yuyu流の鋭い視点で評価してください。\n"
    f"2. 直近のニュースを踏まえた、短期的・長期的な展望を解説してください。\n"
    f"3. 長期投資の観点から、具体的に『何ドルまでなら割安と言えるか（買い増し推奨価格）』を根拠とともに提示してください。\n\n"
    f"※SNSやブログ用のキャッチコピー案は不要です。分析結果のみを、親しみやすくもプロらしい日本語で詳しく回答してください。"
)
            
            response = model.generate_content(prompt)

            # 結果表示
            st.success("分析が完了しました！")
            st.markdown("---")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"詳細エラー: {e}") # これで本当の原因（401, 404, 429など）が見えます

st.markdown("---")
st.info("※この分析はAIによる予測であり、投資の最終決定はご自身の判断で行ってください。")
