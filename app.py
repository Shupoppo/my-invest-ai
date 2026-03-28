import streamlit as st
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# アプリの基本設定
st.set_page_config(page_title="AI投資アナリスト yuyu", layout="centered")
st.title("📈 AI投資診断アプリ by yuyu")
st.caption("世界最新のAIモデルによる銘柄分析（ROE・EPS・最新ニュース重視）")

# --- 1. セキュリティ設定（Secretsから読み込み） ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    finnhub_key = st.secrets["FINNHUB_API_KEY"]
    genai.configure(api_key=gemini_key)
except Exception:
    st.error("システム設定エラー：APIキーが見つかりません。")
    st.stop()

# --- 2. AI分析関数（キャッシュ機能：1時間保存） ---
# ttl=3600 は 3600秒（1時間）という意味です
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_analysis(ticker_symbol, info_dict, news_text):
    # yuyuさんのリストにあった最新モデルを指定
    model = genai.Generative_model("gemini-2.0-flash") 
    
    prompt = (
        f"あなたはプロの投資家『yuyu』として、ブログやYouTubeの視聴者に語りかけるように回答してください。\n\n"
        f"【分析データ】\n"
        f"銘柄: {ticker_symbol}\n"
        f"現在価格: ${info_dict.get('currentPrice', '不明')}\n"
        f"ROE: {info_dict.get('returnOnEquity', 0)*100:.2f}%\n"
        f"EPS成長率: {info_dict.get('earningsGrowth', 0)*100:.2f}%\n"
        f"PER: {info_dict.get('forwardPE', '不明')}\n"
        f"ニュース概要: {news_text}\n\n"
        f"【依頼】\n"
        f"1. ROEとEPSの推移から見た企業の「稼ぐ力」を、yuyu流の鋭い視点で評価してください。\n"
        f"2. 直近のニュースを踏まえた、短期的・長期的な展望を解説してください。\n"
        f"3. 長期投資の観点から、具体的に『何ドルまでなら割安と言えるか（買い増し推奨価格）』を根拠とともに提示してください。\n\n"
        f"※SNSやブログ用のキャッチコピー案は不要です。分析結果のみを、親しみやすくもプロらしい日本語で詳しく回答してください。"
    )
    
    response = model.generate_content(prompt)
    return response.text

# --- 3. ユーザー入力 ---
raw_input = st.text_input("銘柄コード (例: AAPL, 7203, NVDA)", "NVDA").strip()

# 日本株の自動補完 (.T付与)
if raw_input.isdigit() and len(raw_input) == 4:
    ticker = f"{raw_input}.T"
else:
    ticker = raw_input.upper()

# 注意書き（エラー対策）
st.warning("""
**⚠️ ご利用上の注意** 現在、無料枠で運営しているため、アクセスが集中すると「429 Quota Exceeded」というエラーが出ることがあります。その場合は、**1〜5分ほど時間を置いてから**再度実行してみてください。
""")

# --- 4. 実行ボタン ---
if st.button("AIフル分析を実行"):
    try:
        with st.spinner(f"最新モデルで {ticker} を多角的に分析中..."):
            # データ取得
            stock = yf.Ticker(ticker)
            info = stock.info
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
            news_summary = "\n".join([f"- {n['headline']}" for n in news[:5]]) if news else "直近の重要ニュースなし"

            # キャッシュ機能付きのAI分析を呼び出し
            analysis_result = get_ai_analysis(ticker, info, news_summary)

            # 結果表示
            st.success(f"{ticker} の分析が完了しました！")
            st.markdown("---")
            st.markdown(analysis_result)
            
    except Exception as e:
        st.error(f"詳細エラー: {e}")

# --- 5. 免責事項とブログ誘導 ---
st.markdown("---")
st.info("※この分析はAIによる予測であり、投資の最終決定はご自身の判断で行ってください。")

st.markdown("---")
st.write("💡 **最新の銘柄分析や投資戦略はブログで詳しく解説中！**")
st.link_button("📝 yuyuの投資ブログをチェックする", "https://bodymoneymakers.com/")

st.caption("© 2026 AI投資アナリスト yuyu - 投資は自己責任でお願いします。")
