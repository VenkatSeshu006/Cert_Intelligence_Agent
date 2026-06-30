from openai import OpenAI
from config.settings import Settings


class OpenRouterClient:

    def __init__(self):
        self.client = OpenAI(
            api_key=Settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

    def ask(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=Settings.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
