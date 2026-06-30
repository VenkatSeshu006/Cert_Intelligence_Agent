from google import genai
from config.settings import Settings


class GeminiClient:

    def __init__(self):
        self.client = genai.Client(api_key=Settings.GEMINI_API_KEY)

    def ask(self, system_prompt, user_prompt):
        response = self.client.models.generate_content(
            model=Settings.MODEL,
            contents=f"{system_prompt}\n\n{user_prompt}"
        )
        return response.text