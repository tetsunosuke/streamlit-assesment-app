import streamlit as st
import logging
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from modules.gemini_client import GeminiClient
from modules.logger import logger
from modules.google_sheets_handler import add_google_sheets_handler

# --- Google Sheets Loggerのセットアップ ---
add_google_sheets_handler(
    logger_instance=logger,
    sheet_id='13Q4ovS5HKXh9qGnHMrePC9o8Gqute1HuBOvmJqW3cKo',
    worksheet_name='log',
    credentials_key='google_sheets',
    min_level=logging.INFO
)

# デバッグモードの読み込み
# st.secrets を優先し、なければ環境変数を参照、デフォルトは 'False'
debug_val = st.secrets.get("DEBUG_MODE")
if debug_val is None:
    debug_val = os.getenv('DEBUG_MODE', 'False')

debug_mode = str(debug_val).lower() in ('true', '1', 't')

if debug_mode:
    logger.warning("--- DEBUG MODE IS ENABLED ---")

# --- ページ設定 ---
st.set_page_config(
    page_title="メンターAI",
    page_icon="🌱",
    layout="centered"
)

# --- セッション状態の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

if "is_started" not in st.session_state:
    st.session_state.is_started = False

# --- サイドバー: ユーザー設定 ---
with st.sidebar:
    st.header("設定")
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    st.text_input("お名前（ニックネーム可）", key="user_name", disabled=st.session_state.is_started)

# --- メイン画面 ---
st.title("🌱 メンター型アセスメント")
st.markdown("あなたの強みと補完すべき能力を診断します。対話するように回答してください。")

# --- Secrets/Configの読み込み ---
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
model_name = st.secrets.get("GEMINI_MODEL")

if api_key and model_name:
    if os.environ.get("STREAMLIT_SERVER_RUNNING_IN_CLOUD"):
        logger.debug("Secrets loaded from Streamlit Cloud Secrets.", extra={'category': 'System'})
    else:
        logger.debug("Secrets loaded from local .streamlit/secrets.toml.", extra={'category': 'System'})
else:
    logger.warning("Secrets not fully loaded from st.secrets. Attempting fallback to environment variables.")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    if api_key and model_name:
        logger.debug("Secrets loaded from environment variables.", extra={'category': 'System'})
    else:
        if not debug_mode:
            error_message = "APIキーまたはモデル名が設定されていません。st.secretsまたは環境変数を確認してください。"
            logger.error(error_message)
            st.error(f"{error_message}")
            st.stop()
        else:
            logger.warning("Debug mode: API Key and Model Name not loaded, proceeding with mock values.")
            api_key = "mock_api_key_for_debug"
            model_name = "mock_gemini_model_for_debug"

# --- 開始ボタンの表示 ---
if not st.session_state.is_started:
    st.info("左側のサイドバーで名前を入力し、「アセスメントを開始する」ボタンを押してください。")
    if st.button("アセスメントを開始する", type="primary"):
        if not st.session_state.user_name.strip():
            st.warning("お名前を入力してください。")
        else:
            st.session_state.is_started = True
            st.rerun()

# --- チャットロジック (開始後のみ実行) ---
if st.session_state.is_started:
    # 初回起動時（メッセージ履歴が空の場合）の処理
    if not st.session_state.messages:
        try:
            logger.info(f"Starting new session Username:{st.session_state.user_name}.", extra={'category': 'System'})
            
            initial_prompt = f"ユーザーの{st.session_state.user_name}さんが参加しました。アセスメントを開始してください。"

            if not debug_mode:
                # クライアントを都度作成（ステートレス動作）
                client = GeminiClient(api_key=api_key, model_name=model_name)
                # 履歴なしでチャット開始
                chat = client.start_chat(history=[])
                # 初期プロンプト送信
                initial_response = client.send_message(chat, initial_prompt)
                
                # Gemini用の履歴を保存 (辞書形式)
                st.session_state.gemini_history.append({"role": "user", "parts": [{"text": initial_prompt}]})
                st.session_state.gemini_history.append({"role": "model", "parts": [{"text": initial_response.text}]})
                
                initial_text = initial_response.text
            else:
                initial_text = f"デバッグモードで起動しました。アセスメントを開始します。(起動時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            
            # UI用履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": initial_text})
            logger.info(initial_text, extra={'category': 'AI'})
            
        except Exception as e:
            logger.error(f"モデルのセットアップ中にエラーが発生しました: {e}", exc_info=True)
            st.error(f"初期化エラーが発生しました。詳細はログを確認してください。")
            st.stop()


    # チャット履歴の表示
    for msg in st.session_state.messages:
        avatar = "🌱" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            # 終了タグを非表示にする
            display_content = msg["content"].replace("[[END_OF_ASSESSMENT]]", "")
            st.markdown(display_content)

    # ユーザー入力エリア
    if prompt := st.chat_input("回答を入力してください..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # AIの応答を生成
        try:
            with st.chat_message("assistant", avatar="🌱"):
                response_placeholder = st.empty()
                response_placeholder.markdown("🌀 分析中...")
                
                if debug_mode:
                    def mock_response_generator():
                        import time
                        mock_text = f"Debug response at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        time.sleep(1)
                        class MockChunk:
                            def __init__(self, text):
                                self.text = text
                        yield MockChunk(text=mock_text)
                    response = mock_response_generator()
                    full_text = ""
                    for chunk in response:
                        full_text += chunk.text
                        response_placeholder.markdown(full_text + "▌")
                    response_placeholder.markdown(full_text)
                else:
                    # ステートレス: クライアント作成と履歴復元
                    client = GeminiClient(api_key=api_key, model_name=model_name)
                    chat = client.start_chat(history=st.session_state.gemini_history)
                    
                    response = client.send_message(chat, prompt, stream=True)
                
                    full_text = ""
                    for chunk in response:
                        full_text += chunk.text
                        response_placeholder.markdown(full_text.replace("[[END_OF_ASSESSMENT]]", "") + "▌")
                    
                    clean_text = full_text.replace("[[END_OF_ASSESSMENT]]", "")
                    response_placeholder.markdown(clean_text)
                    
                    # Gemini履歴の更新 (辞書形式)
                    st.session_state.gemini_history.append({"role": "user", "parts": [{"text": prompt}]})
                    st.session_state.gemini_history.append({"role": "model", "parts": [{"text": full_text}]})

            st.session_state.messages.append({"role": "assistant", "content": full_text})
            logger.info(prompt, extra={'category': 'User'})
            logger.info(full_text, extra={'category': 'AI'})
        except Exception as e:
            logger.error(f"AIの応答生成中にエラーが発生しました (User: {st.session_state.user_name}): {e}", exc_info=True)
            st.error("AIの応答生成中にエラーが発生しました。もう一度お試しください。")

    # --- アセスメント終了判定とログダウンロード ---
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant" and "[[END_OF_ASSESSMENT]]" in last_msg["content"]:
            st.success("アセスメントが終了しました。お疲れ様でした！")
            st.markdown("以下のボタンから、ここまでの対話ログをダウンロードできます。")
            
            # CSV生成
            import csv
            import io
            
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["Role", "Content"]) # Header
            
            for msg in st.session_state.messages:
                writer.writerow([msg["role"], msg["content"]])
            
            csv_data = csv_buffer.getvalue().encode("utf-8")
            
            st.download_button(
                label="対話ログをダウンロード (CSV)",
                data=csv_data,
                file_name=f"assessment_log_{st.session_state.user_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )