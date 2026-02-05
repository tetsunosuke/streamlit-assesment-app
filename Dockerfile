# 1. Python 3.12 の軽量イメージをベースにする
FROM python:3.12-slim

# 2. 作業ディレクトリを設定
WORKDIR /app

# 3. 依存ライブラリのインストール
# キャッシュを利用してビルド時間を短縮
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. アプリケーションの全ファイルをコピー
COPY . .

# 5. Cloud Run はポート8080で待ち受ける必要があるため、その設定
EXPOSE 8080

# 6. アプリの起動コマンド
# server.address=0.0.0.0 は外部アクセス許可、server.port=8080 はCloud Runの規約
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
