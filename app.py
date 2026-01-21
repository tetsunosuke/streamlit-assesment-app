import streamlit as st
import os
import datetime
from dotenv import load_dotenv
from modules.gemini_client import GeminiClient
from modules.logger import logger

# .envファイルのパスを明示的に指定して環境変数を読み込む
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- ページ設定 ---
st.set_page_config(
    page_title="中堅社員向けメンターAI",
    page_icon="🌱",
    layout="centered"
)

# --- サイドバー: ユーザー設定 ---
with st.sidebar:
    st.header("設定")
    user_name = st.text_input("お名前（ニックネーム可）", value="ゲスト")
    
    if st.button("リセット"):
        logger.info(f"User: {user_name} | Chat reset.")
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.session_state.is_finished = False
        st.rerun()

# --- セッション状態の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

if "is_finished" not in st.session_state:
    st.session_state.is_finished = False

# --- メイン画面 ---
st.title("🌱 中堅社員向け メンター型アセスメント")
st.markdown("あなたの強みと補完すべき能力を診断します。メンターと対話するように回答してください。")

# --- Secrets/Configの読み込み ---
# Streamlit CloudのSecrets、またはローカルの.envファイルから設定を読み込む
if "GOOGLE_API_KEY" in st.secrets and "GEMINI_MODEL" in st.secrets:
    logger.info("Loading secrets from Streamlit Secrets.")
    api_key = st.secrets["GOOGLE_API_KEY"]
    model_name = st.secrets["GEMINI_MODEL"]
else:
    logger.info("Loading secrets from .env file for local development.")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

# APIキーまたはモデル名がない場合の警告
if not api_key or not model_name:
    error_message = "APIキーまたはモデル名が設定されていません。"
    logger.error(error_message)
    st.error(f"{error_message} Streamlit Cloudの場合はSecretsを、ローカル環境の場合は.envファイルを確認してください。")
    st.stop()

# モデルのセットアップ（初回のみ）
if st.session_state.chat_session is None:
    try:
        logger.info(f"User: {user_name} | Starting new session.")
        client = GeminiClient(api_key=api_key, model_name=model_name)
        st.session_state.chat_session = client.start_chat()
        
        # 最初の挨拶をAIから生成させる
        with st.spinner("接続中..."):
            initial_response = client.send_message(
                st.session_state.chat_session, 
                f"ユーザーの{user_name}さんが参加しました。アセスメントを開始してください。"
            )
            st.session_state.messages.append({"role": "assistant", "content": initial_response.text})
            logger.info(f"User: {user_name} | Initial response received.")
    except Exception as e:
        logger.error(f"モデルのセットアップ中にエラーが発生しました: {e}", exc_info=True)
        st.error(f"初期化エラーが発生しました。詳細はログを確認してください。")
        st.stop()

# チャット履歴の表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ユーザー入力エリア
if not st.session_state.is_finished:
    if prompt := st.chat_input("回答を入力してください..."):
        # ユーザーの入力を表示
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # AIの応答を生成
        try:
            with st.spinner("分析中..."):
                client = GeminiClient(api_key=api_key, model_name=model_name)
                response = client.send_message(st.session_state.chat_session, prompt, stream=True)
                
                # AIの応答を表示
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_text = ""
                    for chunk in response:
                        full_text += chunk.text
                        response_placeholder.markdown(full_text.replace("[[END_OF_ASSESSMENT]]", "") + "▌")
                    
                    # 終了判定
                    if "[[END_OF_ASSESSMENT]]" in full_text:
                        st.session_state.is_finished = True
                    
                    clean_text = full_text.replace("[[END_OF_ASSESSMENT]]", "")
                    response_placeholder.markdown(clean_text)

                st.session_state.messages.append({"role": "assistant", "content": clean_text})
                
                # ログ保存
                logger.info(f"User: {user_name} | Prompt: {prompt}")
                logger.info(f"User: {user_name} | AI Response: {clean_text}")

                if st.session_state.is_finished:
                    logger.info(f"User: {user_name} | Assessment Finished.")
                    st.success("アセスメントが終了しました！お疲れ様でした。")
                    st.button("診断結果を詳しく見る（開発中）") # おまけ
                    # st.rerun() # 自動リランするとメッセージが消えることがあるので注意
        except Exception as e:
            logger.error(f"AIの応答生成中にエラーが発生しました (User: {user_name}): {e}", exc_info=True)
            st.error("AIの応答生成中にエラーが発生しました。もう一度お試しください。")

else:
    st.info("アセスメントは終了しました。")
    st.button("新しく開始する", on_click=lambda: st.session_state.update(messages=[], chat_session=None, is_finished=False))
