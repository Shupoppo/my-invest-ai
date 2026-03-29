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
        st.markdown("---")
        st.info("💡 有料会員になると、回数無制限で『買い増し推奨価格』を表示します。")
    else:
        st.write(f"👤 **{st.session_state.user_info['name']} 様**")
        st.success("プレミアム権限：有効")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.rerun()

# --- 4. メイン画面 ---
st.title("📈 AI投資診断アプリ by yuyu")
st.caption("2000万円を運用するブロガーyuyuの視点をAIで再現")

# プレミアム判定
is_premium = st.session_state.authenticated

# --- 💎 プラン説明セクション ---
if not is_premium:
    with st.expander("🚀 プラン内容の比較（無料 vs 有料）", expanded=True):
        st.write("あなたの投資判断を加速させる、2つのプランをご用意しています。")
        plan_data = {
            "機能": ["分析回数", "買い増し推奨価格", "最新ニュース分析", "yuyu流 投資戦略"],
            "無料プラン": ["1日 3回まで", "❌ 非表示", "❌ 簡易表示", "❌ 一部制限"],
            "Premium版": ["✨ 無制限", "✅ ズバリ提示", "✅ 詳細解説", "✅ フル解放"]
        }
        st.table(pd.DataFrame(plan_data))
        st.link_button("💎 月額500円でPremium版に申し込む", "https://bodymoneymakers.com/premium")

# --- 5. 入力セクション ---
raw_input = st.text_input("銘柄コードを入力 (例: AAPL, NVDA, 7203)", "NVDA").strip()
ticker = f"{raw_input}.T" if (raw_input.isdigit() and len(raw_input) == 4) else raw_input.upper()

if not is_premium:
    remaining = max(0, 3 - st.session_state.usage_count)
    st.info(f"💡 無料版：本日の残り利用回数 {remaining} 回")

# --- 6. 分析実行 ---
if st.button("AIフル分析を実行"):
    if not is_premium and st.session_state.usage_count >= 3:
        st.error("本日の無料枠上限（3回）を超えました。")
        st.markdown("### 💎 Premium版で制限を解除しませんか？")
        st.write("Premium版なら、今すぐ回数無制限で『買い増し推奨価格』までズバリ表示します。")
        st.link_button("👉 プレミアム登録で今すぐ分析する", "https://bodymoneymakers.com/premium")
    else:
        try:
            with st.spinner("AIが市場データを解析中..."):
                # データ取得
                stock = yf.Ticker(ticker)
                info = stock.info
                if not info or 'symbol' not in info:
                    st.error(f"銘柄 '{ticker}' のデータが見つかりません。")
                    st.stop()

                roe = (info.get('returnOnEquity', 0) * 100)
                eps_g = (info.get('earningsGrowth', 0) * 100)
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                currency = info.get('currency', 'USD')

                # ニュース取得
                news_text = "直近の重要ニュースは取得されませんでした。"
                try:
                    f_client = finnhub.Client(api_key=st.secrets["FINNHUB_API_KEY"])
                    start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    end = datetime.now().strftime('%Y-%m-%d')
                    news = f_client.company_news(ticker, _from=start, to=end)
                    if news:
                        news_text = "\n".join([f"- {n['headline']}" for n in news[:3]])
                except:
                    pass

                # AI実行
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                if is_premium:
                    prompt = (
                        f"あなたは投資家yuyuです。証券営業の経験を活かし、客観的なデータに基づき回答してください。\n"
                        f"銘柄:{ticker}、現在価格:{current_price}{currency}、ROE:{roe:.2f}%、EPS成長:{eps_g:.2f}%。\n"
                        f"ニュース:{news_text}\n\n"
                        f"【依頼】企業の稼ぐ力と今後の展望、そして『何ドル（何円）までなら上がっても割安と言えるか』を論理的に解説してください。\n"
                        f"【重要指示】回答の最後は必ず『さらに詳しい銘柄分析や私のポートフォリオ戦略については、ブログ「bodymoneymakers.com」で詳しく解説しています。ぜひチェックしてください！』という一文で締めてください。"
                    )
                else:
                    prompt = (
                        f"銘柄:{ticker}の稼ぐ力をROE:{roe:.2f}%等のデータから100文字で評価し、"
                        f"最後に『Premium版なら具体的な買い増し推奨価格も表示します。』と案内を添えてください。"
                    )

                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.subheader(f"📊 {ticker} の分析レポート")
                st.markdown(response.text)
                
                # --- ブログ・免責事項 ---
                st.link_button("🚀 yuyuの最新投資ブログを読む", "https://bodymoneymakers.com/")
                st.warning("⚠️ **免責事項**：本分析はAIによるシミュレーションであり投資成果を保証しません。判断は自己責任でお願いいたします。")
                
                if not is_premium:
                    st.session_state.usage_count += 1

        except Exception as e:
            st.error(f"分析に失敗しました。詳細: {e}")

# --- 7. 共通フッター ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.write("💡 **最新の投資戦略をチェック**")
    st.link_button("📝 公式ブログへ", "https://bodymoneymakers.com/")
with col2:
    st.write("💎 **会員限定コンテンツ**")
    st.link_button("👑 プレミアム詳細", "https://bodymoneymakers.com/premium")

with st.expander("📝 投資に関する重要事項（免責事項）"):
    st.write("""
    本サービスの情報は情報提供のみを目的としており、投資勧誘ではありません。
    投資の最終決定はご自身の判断で行ってください。データの正確性やAIの推測について一切の責任を負いません。
    """)
st.caption("© 2026 AI投資アナリスト yuyu | 投資は自己責任でお願いいたします。")
