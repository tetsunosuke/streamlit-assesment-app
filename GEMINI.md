# プロジェクト概要: 中堅社員向けアセスメントAIアプリ

## 1. プロジェクト概要
企業の「中堅社員（チームの中核人材）」を対象とした、メンター型アセスメントAIアプリケーションを開発する。
ユーザーはWebブラウザ上でAIメンターと対話し、4つの業務シミュレーション（Module）をクリアすることで、自身の強み・弱み・推奨される学習テーマのフィードバックを受け取る。

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
    - `messages`: UI表示用の会話履歴リスト (Raw contentとClean contentを区別して保持)
    - `gemini_history`: Gemini APIとの通信用履歴
    - `is_started`: アセスメント開始フラグ
    - `is_finished`: アセスメント終了フラグ
    - `module_scores`: 各モジュールのスコア履歴
- **スコアとフィードバックの表示制御**:
    - AIは `[[SCORE:X]]` と `[[RATIONALE:...]]` タグを含む応答を生成する。
    - UI上ではこれらのタグを**非表示**にし、定性的なメッセージのみを表示する。
    - ユーザーが明示的にスコアを求めた場合のみ、AIは対話文としてスコアを解説する。
- **ログ機能 (CSV)**:
    - 終了時にダウンロード可能なCSVログを提供する。
    - カラム: `Timestamp`, `Role`, `Content`
    - `Content` には、UIで非表示にされた `[[SCORE]]` や `[[RATIONALE]]` を含む **Raw Content** を記録する。

### 4.2 Gemini API連携 (modules/gemini_client.py)
- `google-genai` (v1.0+) ライブラリを使用。
- ステートレスなセッション復元に対応。

### 4.3 システムプロンプト (modules/prompts.py)
- **スコアリング**: 各モジュールの評価時に3つのサブ評価項目（Sub-criteria）を分析し、総合点(1-10)を算出する。
- **隠しタグ**: 詳細評価は `[[RATIONALE:...]]` 内に記述させ、UIには表示させない運用とする。
- **構成**:
    - Module 1-3: 実務シミュレーション
    - Module 4: プロテジェ効果（知識の形式知化・転用）

### 4.4 ログ管理 (modules/logger.py)
- JSON形式で構造化ログを出力（Cloud Logging対応）。

## 5. Google Cloud Runへのデプロイ
（変更なし）

# 進行フローとモジュール定義

## 🧩 Module 1: 業務管理（リソース最適化）
* **状況**: 金曜16:00。Task A(自/プレゼン)、Task B(他/クレーム)、Task C(後/相談)が競合。
* **サブ評価項目**:
    1. **Prioritization**: 緊急度・重要度の判断。
    2. **Stakeholder Mgmt**: 関係者への期待値調整。
    3. **Problem Solving**: リソース活用による解決。

## 🗣️ Module 2: ピア・レビュー（建設的影響力）
* **状況**: プライドの高い先輩Aさんの「イマイチな企画書」へのレビュー。
* **サブ評価項目**:
    1. **Psychological Safety**: 相手の顔を立てる配慮。
    2. **Assertiveness**: リスクを明確に伝える主張力。
    3. **Constructiveness**: 建設的な代替案の提示。

## 📊 Module 3: データ分析（事実に基づく提言）
* **状況**: システム障害の原因について、会社の方針（印象論）とデータ（事実）が食い違っている。
* **サブ評価項目**:
    1. **Fact-Finding**: データの正確な読み取り。
    2. **Critical Thinking**: 前提を疑う批判的思考。
    3. **Proposal Logic**: 合理的な解決策の提案。

## 🎓 Module 4: 知識整理とスキルの転換（プロテジェ効果）
* **Step**: 後輩への業務指導(Step 1) と、そのスキルの汎用化(Step 2)。
* **サブ評価項目**:
    1. **Explication**: 暗黙知の形式知化。
    2. **Generalization**: スキルの抽象化・構造化。
    3. **Reproduction**: 再現性を高める仕組みづくり。

# 総合フィードバック
全モジュール終了後、以下の構成で出力し、最後に `[[END_OF_ASSESSMENT]]` を付与する。
1. 受検者のタイプ命名
2. 能力分析（各モジュールのサブ評価項目に基づく）
3. 上位要件への接続
4. 明日へのアクション
5. メンターの辛口エール
6. 総合スコアの提示
