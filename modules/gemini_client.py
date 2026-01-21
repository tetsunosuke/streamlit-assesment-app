import google.generativeai as genai
from modules.prompts import SYSTEM_PROMPT

class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        
        print(f"--- Using Gemini Model: {model_name} ---") # デバッグ用にモデル名を出力

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT
        )

    def start_chat(self, history=None):
        if history is None:
            history = []
        return self.model.start_chat(history=history)

    def send_message(self, chat_session, message: str, stream: bool = False):
        return chat_session.send_message(message, stream=stream)
