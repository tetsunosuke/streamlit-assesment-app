from google import genai
from google.genai import types
from modules.prompts import SYSTEM_PROMPT

class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        
        print(f"--- Using Gemini Model (google-genai): {model_name} ---") # デバッグ用にモデル名を出力

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def start_chat(self, history=None):
        if history is None:
            history = []
        
        # History format adaptation might be needed if history is not empty.
        # But app.py starts with empty history usually.
        
        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            ),
            history=history
        )
        return chat

    def send_message(self, chat_session, message: str, stream: bool = False):
        if stream:
            return chat_session.send_message_stream(message)
        else:
            return chat_session.send_message(message)