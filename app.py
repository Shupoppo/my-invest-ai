import os
from flask import Flask, render_template, request
import yfinance as yf
import finnhub
import google.generativeai as genai
from datetime import datetime, timedelta

app = Flask(__name__)

# --- APIキーの設定（環境変数から取得することを推奨） ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "YOUR_FINNHUB_API_KEY")

# --- AIとFinnhubの設定 ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest') # Colabで動作確認済みのモデル
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    report_result = None
    ticker_symbol = "AAPL" # 初期値

    if request.method == 'POST':
        ticker_symbol = request.form['ticker'].upper()
        try:
            # 1. データ取得
            stock = yf.Ticker(ticker_symbol)
            info = stock.info

            # ニュース取得（直近7日間）
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            news = finnhub_client.company_news(ticker_symbol, _from=start_date, to=end_date)
            news_list = "\n".join([f"- {n['headline']}" for n in news[:3]]) if news else "直近のニュースはありません。"

            # 2. AIへの指示文
            prompt = f"""
            銘柄: {ticker_symbol}
            現在価格: ${info.get('currentPrice', 'N/A')}
            ROE: {info.get('returnOnEquity', 0)*100:.2f}%
            EPS成長率: {info.get('earningsGrowth', 0)*100:.2f}%
            PER: {info.get('trailingPE', 'N/A')}

            ニュース:
            {news_list}

            上記データを踏まえ、長期投資の観点で「買い増し推奨価格」と「今後の見通し」を日本語で簡潔に教えてください。
            最後にブログ記事用のキャッチーなタイトル案も1つお願いします。
            """

            # 3. AI診断実行
            response = model.generate_content(prompt)
            report_result = response.text

        except Exception as e:
            report_result = f"エラーが発生しました: {e}\nAPIキーが正しく設定されているか、銘柄コードが正しいか確認してください。"

    return render_template('index.html', report=report_result, ticker=ticker_symbol)

if __name__ == '__main__':
    # Colabで実行する場合、port=8000 などを使用すると良い
    # 実際のデプロイでは、通常はウェブサーバー（Gunicornなど）が管理します
    app.run(host='0.0.0.0', port=5000, debug=True)
