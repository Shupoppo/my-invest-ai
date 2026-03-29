import streamlit as st
import pandas as pd
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 0. アプリ基本設定 ---
st.set_page_config(page_title="AI投資アナリスト yuyu Premium", layout="centered")

# --- 1. ユーザーデータベースの読み込み ---
@st.cache_data(ttl=300)
def load_user_data():
    try:
        sheet_url = st.secrets["USER_SHEET_URL"]
        df = pd.read_csv(sheet_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return pd.DataFrame(columns=["username", "password", "name"])

user_db = load_user_data()

# --- 2. セッション状態の初期化 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_info = None
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

# --- 3. サイドバー：ログイン管理 ---
with st.sidebar:
    st.title("💎 Premium Plan")
    if not st.session_state.authenticated:
        st.subheader("🔑 会員ログイン")
        with st.form("login_sidebar"):
            user_input = st.text_input("ユーザーID")
            pw_input = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                u, p = user_input.strip(), pw_input.strip()
                match = user_db[(user_db['username'].astype(str).str.strip() == u) & 
                                (user_db['password'].astype(str).str.strip() == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_info = match.iloc[0]
                    st.rerun()
                else:
                    st.error("IDまたはパスワードが違います")
    else:
        st.write(f"👤 **{st.session_state.user_info['name']} 様**")
        st.success("プレミアム権限：無制限")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.rerun()

# --- 4. メイン画面 ---
st.title("📈 AI投資診断アプリ by yuyu")
is_premium = st.session_state.authenticated

raw_input = st.text_input("銘柄コード (AAPL, NVDA, 7203など)", "NVDA").strip()
ticker = f"{raw_input}.T" if (raw_input.isdigit() and len(raw_input) == 4) else raw_input.upper()

if st.button("AIフル分析を実行"):
    if not is_premium and st.session_state.usage_count >= 3:
        st.error("無料枠上限です。")
    else:
        try:
            with st.spinner("データを取得中..."):
                # ① 株価データ取得
                stock = yf.Ticker(ticker)
                info = stock.info
                if not info or 'symbol' not in info:
                    st.error(f"銘柄 '{ticker}' のデータが見つかりません。")
                    st.stop()

                roe = (info.get('returnOnEquity', 0) * 100)
                eps_g = (info.get('earningsGrowth', 0) * 100)
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                currency = info.get('currency', 'USD')

                # ② ニュース取得 (失敗しても続行)
                news_text = "直近のニュースデータは取得できませんでした。"
                try:
                    f_client = finnhub.Client(api_key=st.secrets["FINNHUB_API_KEY"])
                    start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    end = datetime.now().strftime('%Y-%m-%d')
                    news = f_client.company_news(ticker, _from=start, to=end)
                    if news:
                        news_text = "\n".join([f"- {n['headline']}" for n in news[:3]])
                except:
                    pass

                # ③ AI分析実行
                st.write("📖 AIが文章を作成中...")
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = (
                    f"あなたは投資家yuyuです。銘柄:{ticker}、現在価格:{current_price}{currency}、"
                    f"ROE:{roe:.2f}%、EPS成長:{eps_g:.2f}%のデータを元に、"
                    f"この企業の『稼ぐ力』と『買い増し推奨価格』を、証券マンの視点で詳しく解説してください。\n"
                    f"ニュース背景:\n{news_text}"
                )
                
                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.subheader(f"📊 {ticker} の分析結果")
                st.markdown(response.text)
                
                if not is_premium:
                    st.session_state.usage_count += 1

        except Exception as e:
            st.error(f"予期せぬエラーが発生しました。しばらく待ってから再度お試しください。\nエラー詳細: {e}")

st.caption("© 2026 AI投資アナリスト yuyu")
