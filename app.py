import streamlit as st
import pandas as pd
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 0. アプリ基本設定 ---
st.set_page_config(page_title="AI投資アナリスト yuyu Premium", layout="centered")

# --- 1. ユーザーデータベースの読み込み ---
@st.cache_data(ttl=60) # 反映を速めるためTTLを短縮
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

# --- 3. サイドバー：ログイン管理 & プレミアム導線 ---
with st.sidebar:
    st.title("💎 Premium Plan")
    if not st.session_state.authenticated:
        st.subheader("🔑 会員ログイン")
        with st.form("login_sidebar"):
            user_input = st.text_input("ユーザーID（メールアドレス）")
            pw_input = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                u, p = user_input.strip(), pw_input.strip()
                # 名簿と照合
                match = user_db[(user_db['username'].astype(str).str.strip() == u) & 
                                (user_db['password'].astype(str).str.strip() == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_info = match.iloc[0]
                    st.rerun()
                else:
                    st.error("IDまたはパスワードが違います")
        
        st.markdown("---")
        st.subheader("🌟 プレミアム未加入の方")
        st.info("有料会員は回数無制限。AIが『買い増し推奨価格』をズバリ提示します。")
        
        # 確定した詳細ページURLへリダイレクト
        detail_url = "https://bodymoneymakers.com/ai%e6%8a%95%e8%b3%87%e3%82%a2%e3%83%8a%e3%83%aa%e3%82%b9%e3%83%88-yuyu-premium-%e8%a9%b3%e7%b4%b0/"
        if st.button("プレミアム詳細・お申し込み"):
            js = f"window.open('{detail_url}')"
            st.components.v1.html(f'<script>{js}</script>', height=0)
            
    else:
        st.write(f"👤 **{st.session_state.user_info['name']} 様**")
        st.success("プレミアム権限：有効")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    if st.button("🔄 最新の名簿を読み込む"):
        st.cache_data.clear()
        st.rerun()

# --- 4. メイン画面 ---
st.title("📈 AI投資診断アプリ by yuyu")
is_premium = st.session_state.authenticated

# --- 💎 プラン説明（無料ユーザーのみ表示） ---
if not is_premium:
    with st.expander("🚀 プラン内容の比較（無料 vs 有料）", expanded=True):
        plan_data = {
            "機能": ["分析回数", "買い増し推奨価格", "最新ニュース分析", "フル機能アクセス"],
            "無料版": ["1日 3回まで", "❌ 非表示", "❌ 簡易表示", "❌ 制限あり"],
            "Premium版": ["✨ 無制限", "✅ ズバリ提示", "✅ 詳細解説", "✅ フル解放"]
        }
        st.table(pd.DataFrame(plan_data))
        # 詳細ページへのボタン
        st.link_button("💎 Premium版の詳細・申し込みはこちら", detail_url)

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
        st.link_button("👉 プレミアム登録で制限を解除する", detail_url)
    else:
        try:
            with st.spinner("AIが財務データと最新ニュースをスキャン中..."):
                # データ取得
                stock = yf.Ticker(ticker)
                info = stock.info
                if not info or 'symbol' not in info:
                    st.error(f"銘柄 '{ticker}' のデータが見つかりません。")
                    st.stop()

                # 財務指標の抽出
                roe = (info.get('returnOnEquity', 0) * 100)
                eps_g = (info.get('earningsGrowth', 0) * 100)
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                currency = info.get('currency', 'USD')
                per = info.get('trailingPE', 0)

                # ニュース取得 (Finnhub)
                news_text = "直近の重要ニュースは取得されませんでした。"
                try:
                    f_client = finnhub.Client(api_key=st.secrets["FINNHUB_API_KEY"])
                    start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    end = datetime.now().strftime('%Y-%m-%d')
                    news = f_client.company_news(ticker, _from=start, to=end)
                    if news:
                        news_text = "\n".join([f"- {n['headline']}" for n in news[:3]])
                except: pass

                # AI接続設定
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # 証券マン yuyu プロンプト（プレミアム用）
                if is_premium:
                    prompt = (
                        f"あなたは2000万円を運用する投資家yuyuです。証券営業の経験を活かし、プロの視点で回答してください。\n"
                        f"銘柄:{ticker}、価格:{current_price}{currency}、ROE:{roe:.2f}%、EPS成長:{eps_g:.2f}%、PER:{per:.2f}倍。\n"
                        f"最新ニュース:{news_text}\n\n"
                        f"【依頼】\n"
                        f"1. ROEとEPS成長率に基づき、この企業の『稼ぐ力』を厳しく評価してください。\n"
                        f"2. 最新ニュースが株価に与える影響を解説してください。\n"
                        f"3. 『何ドル（何円）までなら上がっても割安で買えるか』、目標買い増し価格を論理的に提示してください。\n"
                        f"4. 最後に『さらに詳しい銘柄分析や投資戦略については、ブログ「bodymoneymakers.com」で解説しています。ぜひチェックしてください！』と締めてください。"
                    )
                else:
                    prompt = (
                        f"銘柄:{ticker}の稼ぐ力を財務データ(ROE:{roe:.2f}%, EPS成長:{eps_g:.2f}%)から100文字程度で評価してください。"
                        f"最後に『Premium版なら具体的な買い増し推奨価格も表示します。』と案内を添えてください。"
                    )

                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.subheader(f"📊 {ticker} の分析レポート")
                st.markdown(response.text)
                
                # アクション誘導
                st.link_button("🚀 yuyuの最新投資ブログを読む", "https://bodymoneymakers.com/")
                
                if not is_premium:
                    st.session_state.usage_count += 1

        except Exception as e:
            st.error(f"分析エラー: {e}")

# --- 7. 共通フッター ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.write("💡 **最新の投資戦略をチェック**")
    st.link_button("📝 公式ブログへ", "https://bodymoneymakers.com/")
with col2:
    st.write("💎 **会員限定コンテンツ**")
    st.link_button("👑 プレミアム詳細ページへ", detail_url)

st.caption("© 2026 AI投資アナリスト yuyu | 投資は自己責任でお願いいたします。")
