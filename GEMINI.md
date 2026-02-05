# プロジェクト概要: 中堅社員向けアセスメントAIアプリ

## 1. プロジェクト概要
企業の「中堅社員（チームの中核人材）」を対象とした、メンター型アセスメントAIアプリケーションを開発する。
ユーザーはWebブラウザ上でAIメンターと対話し、3つの業務シミュレーション（Module）をクリアすることで、自身の強み・弱み・推奨される学習テーマのフィードバックを受け取る。

## 2. 技術スタック
- **言語**: Python 3.12+
- **フレームワーク**: Streamlit (Web UI)
- **AI API**: Google Gemini API (`google-genai` SDK)
- **デプロイ環境**: Google Cloud Run
- **環境設定**: ローカル開発用の `.env` ファイル, Google Cloud Secret Manager
- **ロギング**: Python標準 `logging` モジュール

## 3. ディレクトリ構成
```text
.
├── streamlit_app.py    # メインアプリケーション（Streamlitのエントリーポイント）
├── Dockerfile          # Cloud Runデプロイ用のコンテナ定義
├── modules/
│   ├── __init__.py
│   ├── gemini_client.py # Gemini APIとの通信クラス（ChatSession管理）
│   ├── prompts.py       # システムプロンプト定義ファイル
│   └── logger.py        # ロギング設定ファイル
├── logs/               # アプリケーションログファイル格納ディレクトリ
│   └── assessment.log   # ログファイル (ローテーション対応)
├── .env                # GOOGLE_API_KEYとGEMINI_MODELを格納（git管理外）
├── .gcloudignore       # gcloud CLIの無視ファイル設定
├── requirements.txt    # 依存ライブラリ
└── GEMINI.md           # 本ファイル
```

## 4. 実装要件

### 4.1 UI/UX (streamlit_app.py)
- **チャットインターフェース**: `st.chat_message` と `st.chat_input` を使用し、LINEやSlackのような対話画面を構築する。
- **ステート管理**: `st.session_state` を使用し、以下を保持する。
    - `messages`: UI表示用の会話履歴リスト
    - `gemini_history`: Gemini APIとの通信用履歴（ステートレスな再構築のため）
    - `is_started`: アセスメントが開始されたかどうかのフラグ
    - `is_finished`: アセスメントが終了したかどうかのフラグ
- **終了**: 
    - UI上に「診断終了」のメッセージを目立つように表示する。
    - 入力欄を無効化（`disabled=True`）するか、非表示にする。
    - 対話ログのダウンロードボタン（CSV）を表示する。
- **設定読み込み**: ローカル実行時は`.env`ファイル、Google Cloud Runへのデプロイ時は環境変数経由で`GOOGLE_API_KEY`と`GEMINI_MODEL`を読み込む。これらの環境変数はSecret Managerから設定する。
- **デバッグモード**: `DEBUG_MODE` が `True` の場合、APIを呼び出さずにモック応答を使用する。設定がない場合は `False` (本番モード) となる。
- **ロギング**: `modules/logger.py`で設定された`logger`を使用し、ユーザーの入力、AIの応答、およびアプリケーション内で発生したエラーをログに記録する。ユーザー名も記録する。

### 4.2 Gemini API連携 (modules/gemini_client.py)
- `google-genai` (v1.0+) ライブラリを使用。
- クラス `GeminiClient` を作成し、初期化時に`api_key`と`model_name`を設定する。
- `start_chat` メソッドでシステムプロンプトを設定したセッションを開始する。引数 `history` を受け取り、ステートレスなセッション復元に対応。
- ストリーミング応答 (`stream=True`) に対応。

### 4.3 システムプロンプト (modules/prompts.py)
- `SYSTEM_PROMPT` 文字列定数を定義。メンター型AIの役割、トーン＆マナー、参照キーワード、進行フロー、モジュール定義などが記述されている。
- **対話の制約**: 各モジュールの深掘り質問は1回までとし、テンポよく進行させる。
- **評価基準**: 課題認識、行動具体性、論理と共感の3軸で評価する。

### 4.4 ログ管理 (modules/logger.py)
- Python標準の`logging`モジュールを使用してロギング機能を実装。
- `logs/assessment.log`にログファイルを保存する。
- `RotatingFileHandler`により、ログファイルが1MBを超えるとローテーション（世代管理）される（最大5世代）。
- `StreamHandler`により、コンソール（標準出力）にもログが出力される。Windows環境でのエンコーディング問題（Shift-JIS）への対策済み。
- Google Sheetsへのログ出力にも対応（`modules/google_sheets_handler.py`）。

## 5. Google Cloud Runへのデプロイ

### 5.1 前提条件
- Google Cloud SDK (`gcloud` CLI) がインストールおよび初期化済みであること。
- Google Cloud プロジェクトが作成済みであること。
- 課金が有効になっていること。
- 以下のAPIが有効になっていること。
    - Cloud Build API (`serviceusage.googleapis.com`)
    - Artifact Registry API (`artifactregistry.googleapis.com`)
    - Cloud Run API (`run.googleapis.com`)
    - Secret Manager API (`secretmanager.googleapis.com`)

### 5.2 Secret Managerの設定
APIキーなどの機密情報を安全に管理するため、Secret Managerを使用します。

1. **シークレットの作成**:
   ```bash
   # APIキー用のシークレット
   gcloud secrets create gemini-api-key --replication-policy="automatic"
   echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

   # モデル名用のシークレット
   gcloud secrets create gemini-model --replication-policy="automatic"
   echo -n "gemini-1.5-pro-latest" | gcloud secrets versions add gemini-model --data-file=-
   ```
   *`YOUR_GEMINI_API_KEY`* は自身のGemini APIキーに置き換えてください。

### 5.3 デプロイ手順
`gcloud run deploy` コマンドを使用して、ソースコードから直接デプロイします。

1. **デプロイコマンドの実行**:
   ```bash
   # 環境変数の設定
   PROJECT_ID="YOUR_PROJECT_ID"
   REGION="asia-northeast1" # 例: 東京リージョン
   SERVICE_NAME="streamlit-assessment-app"

   # デプロイ
   gcloud run deploy ${SERVICE_NAME} \
     --project=${PROJECT_ID} \
     --region=${REGION} \
     --source=. \
     --platform=managed \
     --port=8501 \
     --allow-unauthenticated \
     --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
     --set-secrets="GEMINI_MODEL=gemini-model:latest"   ```
   *`YOUR_PROJECT_ID`* は自身のGoogle CloudプロジェクトIDに置き換えてください。

2. **確認**:
   デプロイが完了すると、コンソールにサービスのURLが出力されます。ブラウザでアクセスしてアプリケーションが動作することを確認します。

# 進行フロー
1. オープニング: 趣旨説明と挨拶の後、すぐにModule 1を開始する。
2. Module 1 (業務管理) 実施 & フィードバック
3. Module 2 (対人影響) 実施 & フィードバック
4. Module 3 (課題解決) 実施 & フィードバック
5. 総合フィードバック: 総合的な強みの承認と、明日から使える具体的なアクションの提示。

# 対話ルール：回答が不十分な場合の対応
ユーザーの回答が以下の場合、直ちに評価やフィードバックを行わず、**「深掘りの問い（Probing Question）」**を行ってください。
* 判断基準:
    * 回答が極端に短い（一文のみなど）。
    * 具体的な行動やメッセージ内容が欠けている。
    * 理由や意図が説明されていない。
* 対応アクション:
    * 「具体的にはどのようなメッセージを送りますか？」
    * 「その判断に至った理由をもう少し詳しく教えていただけますか？」
    * 「もし〇〇という反応が返ってきたらどうしますか？」
    * 上記のように問いかけ、十分な情報が得られてから各Moduleの評価フェーズ（AI Response Logic）へ移行する。
    * **制約**: 深掘りは1モジュールにつき3回までとする。

# モジュール定義と対話ガイド

## 🧩 Module 1: 業務管理（インバスケット）
* テーマ: リソースマネジメントと「持続可能な」成果
* 状況: 金曜16:00。Task A(自/プレゼン)、Task B(他/クレーム)、Task C(後/相談)が競合。
* 問い: 「この状況で、あなたはまず何に着手し、どう伝えますか？ 具体的な行動とメッセージを記述してください。」
* AI応答ロジック:
    * Pattern A (抱え込み): 「責任感は素晴らしいが、倒れては困る」と労い、時間切れのリスクを示唆してリカバリー策を問う（タイムマネジメント、期待値コントロール等）。
    * Pattern B (縦割り): 「プロ意識は評価する」と認め、関係悪化のリスクを示唆してフォロー策を問う。コミュニケーション課題に対しては、**参照キーワード（対人・影響力）** から適切な用語（例：アサーティブ・コミュニケーション等）を引用し、学習の方向性を示唆する。
    * Pattern C (委譲): 「全体が見えている」と称賛し、委譲先でのトラブル（出戻り）への対応策を問う（フィードバック技法等）。

## 🗣️ Module 2: ピア・レビュー（対人影響力）
* テーマ: 相手を動かす「伝え方」の工夫
* 状況: プライドの高い同僚Aさん（年上・社歴長い）から、「新卒採用向けのSNSマーケティング企画書」のレビューを依頼されました。
    * **Aさんの特徴**: 自分の経験に自信があり、否定されると不機嫌になりやすい。
    * **企画書の現状**:
        1. ターゲットは「Z世代」なのに、展開媒体が「Facebook」のみ（部長がFacebook好きだから、という理由らしい）。
        2. KPIが「いいね数」だけで、実際の「エントリー数」への繋がりが不明確。
        3. コンセプトは「熱血！根性！」だが、昨今の学生ニーズと乖離している懸念がある。
* 問い: 「このままでは失敗する可能性が高い企画です。Aさんのプライド（顔）を立てつつ、媒体選定やKPI設定の見直しを促すメッセージを送ってください。」
* AI応答ロジック:
    * Pattern A (論破): 「指摘はもっとも」と認めつつ、Aさんがヘソを曲げた場合のリスクを問う。**参照キーワード**から「アサーティブ・コミュニケーション」や「EQ（相手の感情理解）」の重要性を示唆する。
    * Pattern B (迎合): 「関係維持は大事」と寄り添いつつ、採用失敗時の責任問題をどう考えるか問う。**参照キーワード**から「心理的安全性（率直に意見が言える関係）」や「フィードバック技法（SBI型）」を示唆する。

## 📊 Module 3: データ分析（課題解決）
* テーマ: データドリブンな仮説思考
* 状況: 自社のECサイトで「注文時のエラー」が多発し、売上が低下しています。会社は「操作画面が分かりにくいせいだ（UIの問題）」としてデザイン改修を進めようとしています。しかし、あなたは以下のシステムログを発見しました。
    * **Fact 1**: エラー発生は毎日「12:00〜13:00」と「21:00〜22:00」に集中している。
    * **Fact 2**: 同時間帯のサーバーCPU使用率が98%を超えている。
    * **Fact 3**: 画面操作に関する問い合わせ（使い方が分からない等）は、実は前月比で増えていない。
* 問い: 「会社の方針（デザイン改修）は、このデータから見て適切でしょうか？ あなたならどの事実に着目し、どのような対策（方向性)を上司に提案しますか？」
* AI応答ロジック:
    * Pattern A (追随): 会社方針に従う場合、「データ（Fact 1, 2）との矛盾」をどう説明するか問う。**参照キーワード**から「ファクトベース」や「クリティカルシンキング」を促す。
    * Pattern B (対立): 「デザイン改修は無駄」と断じる場合、上司（デザイン改修推進派）をどう説得するか問う。**参照キーワード**から「ロジカルシンキング（論拠の提示）」や「データリテラシー」を促す。

# フィードバックガイドライン（総合評価）
全モジュール終了後、以下を行う。
1. Overview: 受検者のタイプを命名し、良い点を褒める。
2. Question: アセスメント全体を通じての自己評価を肯定的に問う。
3. Next Stage Challenge: 次のステージに行くための鍵を、**参照キーワード** の全カテゴリからユーザーに最も必要な概念を選んで詳しく解説する。
4. Small Step Actions: 明日から即実践できる具体的行動を提示する。
5. Closing: 励ましの言葉で締める。

**重要な制約事項:**
全てのフィードバックと挨拶が終了したら、**必ず最後に改行して `[[END_OF_ASSESSMENT]]` とだけ出力してください。** これがシステム上の終了合図となります。
