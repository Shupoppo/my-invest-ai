import streamlit as st
import pandas as pd
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 0. アプリ基本設定 ---
st.set_page_config(page_title="AI投資アナリスト yuyu Premium", layout="centered")

# --- 1. ユーザーデータベース（Googleスプレッドシート）の読み込み ---
@st.cache_data(ttl=600)
def load_user_data():
    try:
        sheet_url = st.secrets["USER_SHEET_URL"]
        df = pd.read_csv(sheet_url)
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
        st.write("有料会員になると：")
        st.write("✅ 1日の利用回数が**無制限**")
        st.write("✅ yuyu流の**買い増し推奨価格**を表示")
        st.write("✅ 最新ニュースの**詳細分析**を解放")
        st.link_button("👉 有料プランに申し込む", "https://bodymoneymakers.com/premium")
        st.markdown("---")
        st.subheader("🔑 会員ログイン")
        with st.form("login_sidebar"):
            user = st.text_input("ユーザーID")
            pw = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                match = user_db[(user_db['username'].astype(str) == user) & (user_db['password'].astype(str) == pw)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_info = match.iloc[0]
                    st.rerun()
                else:
                    st.error("IDまたはパスワードが違います")
    else:
        st.write(f"👤 **{st.session_state.user_info['name']} 様**")
        st.success("プレミアムプラン適用中")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()

# --- 4. メイン画面 ---
st.title("📈 AI投資診断アプリ by yuyu")
st.caption("最新のAIモデルによる銘柄分析（ROE・EPS・最新ニュース重視）")

is_premium = st.session_state.authenticated
if not is_premium:
    st.info(f"💡 無料版：本日の残り利用回数 {max(0, 3 - st.session_state.usage_count)} 回")

raw_input = st.text_input("銘柄コードを入力 (例: AAPL, 7203, NVDA)", "NVDA").strip()
ticker = f"{raw_input}.T" if (raw_input.isdigit() and len(raw_input) == 4) else raw_input.upper()

# --- 5. 分析実行 ---
if st.button("AIフル分析を実行"):
    if not is_premium and st.session_state.usage_count >= 3:
        st.error("本日の無料枠を超えました。プレミアム会員に登録すると無制限でご利用いただけます！")
        st.link_button("💎 プレミアム会員の登録はこちら", "https://bodymoneymakers.com/premium")
    else:
        try:
            with st.spinner(f"最新のAIが {ticker} を分析中..."):
                # データ取得
                stock = yf.Ticker(ticker)
                info = stock.info
                
                roe_raw = info.get('returnOnEquity')
                roe_percent = (roe_raw * 100) if roe_raw is not None else 0.0
                eps_raw = info.get('earningsGrowth')
                eps_percent = (eps_raw * 100) if eps_raw is not None else 0.0

                # ニュース取得
                news_summary = "直近ニュースなし"
                try:
                    finnhub_client = finnhub.Client(api_key=st.secrets["FINNHUB_API_KEY"])
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
                    if news:
                        news_summary = "\n".join([f"- {n['headline']}" for n in news[:5]])
                except:
                    pass

                # プロンプト設定
                if is_premium:
                    prompt = (
                        f"あなたはプロの投資家『yuyu』として詳細に回答してください。\n"
                        f"銘柄:{ticker}、ROE:{roe_percent:.2f}%、EPS成長:{eps_percent:.2f}%。\n"
                        f"ニュース:{news_summary}\n\n"
                        f"【依頼】ROE/EPS、公表されているIRの決算内容から見た『企業の稼ぐ力』を深掘りし、今後の展望と、具体的な『買い増し推奨価格（何ドルぐらいまでなら上がっても割安で買えるのか）』を根拠とともに詳しく解説してください。"
                    )
                else:
                    prompt = (
                        f"銘柄:{ticker}のROEとEPSから見た『稼ぐ力』を100文字以内で簡潔に評価してください。具体的な推奨価格などの詳細は伏せてください。"
                    )

                # AI実行 (最新のGA版モデル名を指定)
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)

                st.markdown("---")
                st.markdown(response.text)
                
                if not is_premium:
                    st.session_state.usage_count += 1
                    
        except Exception as e:
            st.error(f"分析エラー：銘柄データが見つからないか、APIの制限です。時間をおいて試してください。\n詳細: {e}")

# --- 6. 案内 ---
st.markdown("---")
if not is_premium:
    st.subheader("🚀 さらなる詳細分析が必要ですか？")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**無料版（現在）**")
        st.write("・1日3回まで / 簡易コメント")
    with col2:
        st.write("**プレミアム版（Premium）**")
        st.write("・✨ **回数無制限 / 目標株価解放**")
    st.link_button("💎 プレミアム会員の詳細・登録はこちら", "https://bodymoneymakers.com/premium")

st.info("※投資の最終決定はご自身の判断で行ってください。")
st.write("💡 **最新の投資戦略はブログで解説中！**")
st.link_button("📝 yuyuの投資ブログをチェック", "https://bodymoneymakers.com/")
st.caption("© 2026 AI投資アナリスト yuyu")
