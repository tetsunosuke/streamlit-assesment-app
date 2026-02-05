# 中堅社員向けアセスメントAIアプリ

企業の「中堅社員（チームの中核人材）」を対象とした、メンター型アセスメントAIアプリケーションです。
ユーザーはWebブラウザ上でAIメンターと対話し、3つの業務シミュレーション（Module）をクリアすることで、自身の強み・弱み・推奨される学習テーマのフィードバックを受け取ることができます。

## ✨ 特徴
- **シナリオベースのアセスメント**: リアルな業務に近い3つのシナリオを通して、実践的な課題解決能力を測定します。
- **インタラクティブな対話**: AIメンターとの対話を通して、内省を促し、深い自己理解へと導きます。
- **個別フィードバック**: 各個人の強みと成長課題を特定し、具体的なアクションプランを提示します。

## 🚀 技術スタック
- **言語**: Python 3.12+
- **フレームワーク**: Streamlit
- **AI**: Google Gemini API
- **デプロイ**: Google Cloud Run
- **CI/CD**: (TBD)

## 🛠️ ローカルでの実行方法

1. **リポジトリをクローン**:
   ```bash
   git clone https://github.com/your-username/streamlit-assesment-app.git
   cd streamlit-assesment-app
   ```

2. **仮想環境の作成と有効化**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **依存ライブラリのインストール**:
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数の設定**:
   `.env` ファイルをプロジェクトルートに作成し、以下の内容を記述します。
   ```
   GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
   GEMINI_MODEL="gemini-1.5-pro-latest"
   ```
   `YOUR_GOOGLE_API_KEY` はご自身のAPIキーに置き換えてください。

5. **Streamlitアプリケーションの起動**:
   ```bash
   streamlit run streamlit_app.py
   ```
   ブラウザで `http://localhost:8501` を開きます。

## ☁️ Google Cloud Runへのデプロイ

### 前提条件
- Google Cloud SDK (`gcloud` CLI) がインストールおよび初期化済みであること。
- Google Cloudプロジェクトが作成済みで、課金が有効になっていること。
- 必要なAPI (Cloud Build, Artifact Registry, Cloud Run, Secret Manager) が有効になっていること。

### 1. Secret Managerの設定
APIキー等の機密情報を設定します。

```bash
# APIキー用のシークレット
gcloud secrets create google-api-key --replication-policy="automatic"
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets versions add google-api-key --data-file=-

# モデル名用のシークレット
gcloud secrets create gemini-model --replication-policy="automatic"
echo -n "gemini-1.5-pro-latest" | gcloud secrets versions add gemini-model --data-file=-
```

### 2. デプロイ
`gcloud run deploy` コマンドでソースコードから直接デプロイします。

```bash
# 環境変数の設定
PROJECT_ID="YOUR_PROJECT_ID"
REGION="asia-northeast1" # 東京リージョンの例
SERVICE_NAME="streamlit-assessment-app"

# デプロイ実行
gcloud run deploy ${SERVICE_NAME} \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --source=. \
  --platform=managed \
  --allow-unauthenticated
```

デプロイ完了後、表示されるURLにアクセスします。

## 📝 詳細
より詳細なプロジェクトの仕様や実装要件については、[GEMINI.md](GEMINI.md) を参照してください。
