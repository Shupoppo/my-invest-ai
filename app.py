import streamlit as st
import pandas as pd
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 0. アプリ基本設定 ---
st.set_page_config(page_title="AI投資アナリスト yuyu Premium", layout="centered")

# --- 1. ユーザーデータベース（Googleスプレッドシート）の読み込み ---
@st.cache_data(ttl=300) # キャッシュを5分（300秒）に短縮して反映を速くしました
def load_user_data():
    try:
        sheet_url = st.secrets["USER_SHEET_URL"]
        df = pd.read_csv(sheet_url)
        # カラム名の前後の空白を削除して不一致を防止
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"シート読み込みエラー: {e}")
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
            user_input = st.text_input("ユーザーID（メールアドレス）")
            pw_input = st.text_input("パスワード", type="password")
            submit = st.form_submit_button("ログイン")

            if not st.session_state.authenticated:
        st.subheader("🔑 会員ログイン")
        st.write(f"現在の登録ユーザー数: {len(user_db)}名")
        with st.form("login_sidebar"):
            user_input = st.text_input("ユーザーID（メールアドレス）")
            pw_input = st.text_input("パスワード", type="password")
            submit = st.form_submit_button("ログイン")

            
            if submit:
                # 前後の空白を消して照合（入力ミス防止）
                u = user_input.strip()
                p = pw_input.strip()
                
                match = user_db[(user_db['username'].astype(str).str.strip() == u) & 
                                (user_db['password'].astype(str).str.strip() == p)]
                
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_info = match.iloc[0]
                    st.success(f"ようこそ、{st.session_state.user_info['name']} 様")
                    st.rerun()
                else:
                    st.error("IDまたはパスワードが正しくありません")
        
        st.markdown("---")
        st.write("✨ **有料会員のメリット**")
        st.write("・AI分析が**回数無制限**")
        st.write("・yuyu流 **買い増し推奨価格** を表示")
        st.link_button("👉 有料プランに申し込む", "https://bodymoneymakers.com/premium")
    
    else:
        st.write(f"👤 **{st.session_state.user_info['name']} 様**")
        st.success("プレミアムプラン適用中（無制限）")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()

# --- 4. メイン画面 ---
st.title("📈 AI投資診断アプリ by yuyu")
st.caption("最新のAIモデルによる銘柄分析（ROE・EPS・最新ニュース重視）")

# プレミアム判定
is_premium = st.session_state.authenticated

if not is_premium:
    remaining = max(0, 3 - st.session_state.usage_count)
    st.info(f"💡 無料版：本日の残り利用回数 {remaining} 回")
else:
    st.success("✨ プレミアム権限により、分析回数は無制限です。")

raw_input = st.text_input("銘柄コードを入力 (例: AAPL, 7203, NVDA)", "NVDA").strip()
ticker = f"{raw_input}.T" if (raw_input.isdigit() and len(raw_input) == 4) else raw_input.upper()

# --- 5. 分析実行 ---
if st.button("AIフル分析を実行"):
    # 無料ユーザーかつ回数切れの場合
    if not is_premium and st.session_state.usage_count >= 3:
        st.error("本日の無料枠（3回）を超えました。")
        st.link_button("💎 プレミアム会員登録で制限を解除", "https://bodymoneymakers.com/premium")
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
                news_summary = "直近1週間の重要ニュースなし"
                try:
                    finnhub_client = finnhub.Client(api_key=st.secrets["FINNHUB_API_KEY"])
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    news = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
                    if news:
                        news_summary = "\n".join([f"- {n['headline']}" for n in news[:5]])
                except:
                    pass

                # プロンプト出し分け
                if is_premium:
                    prompt = (
                        f"あなたは2000万円を運用する投資家『yuyu』です。プロの証券マンの視点で詳細に回答してください。\n"
                        f"銘柄:{ticker}、ROE:{roe_percent:.2f}%、EPS成長:{eps_percent:.2f}%。\n"
                        f"最新ニュース:\n{news_summary}\n\n"
                        f"【依頼】ROE・EPS、直近決算から『企業の稼ぐ力』を深掘りし、今後の展望を述べてください。また『何ドル（何円）までなら上がっても割安で買えるのか』という買い増し推奨価格を根拠とともに提示してください。"
                    )
                else:
                    prompt = (
                        f"銘柄:{ticker}のROE({roe_percent:.2f}%)とEPS成長率({eps_percent:.2f}%)から見た企業の稼ぐ力を、100文字以内で簡潔に評価してください。目標価格は含めないでください。"
                    )

                # AI実行 (安定版 gemini-1.5-flash)
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)

                st.markdown("---")
                st.markdown(response.text)
                
                # 分析成功時、無料ユーザーのみカウントアップ
                if not is_premium:
                    st.session_state.usage_count += 1
                    
        except Exception as e:
            st.error(f"分析エラー：銘柄が見つからないか、API制限です。\n詳細: {e}")

# --- 6. 案内 ---
st.markdown("---")
if not is_premium:
    st.subheader("🚀 プレミアム版で制限を解除しませんか？")
    st.write("プレミアム版なら、回数無制限で『買い増し推奨価格』までズバリ表示します。")
    st.link_button("💎 プレミアム会員の詳細・登録はこちら", "https://bodymoneymakers.com/premium")

st.info("※投資の最終決定はご自身の判断で行ってください。")
st.write("💡 **最新の投資戦略はブログで解説中！**")
st.link_button("📝 yuyuの投資ブログをチェック", "https://bodymoneymakers.com/")
st.caption("© 2026 AI投資アナリスト yuyu")
