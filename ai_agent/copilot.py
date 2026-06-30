from ai_agent.client import OpenRouterClient
from ai_agent.memory import Memory
from ai_agent.prompts import SYSTEM_PROMPT


class Copilot:

    def __init__(self, employee):
        self.client = OpenRouterClient()
        self.memory = Memory()
        self.memory.load_employee(employee)

    def chat(self, question):
        self.memory.add_user_message(question)
        prompt = self.memory.build_prompt(question)
        answer = self.client.ask(SYSTEM_PROMPT, prompt)
        self.memory.add_ai_message(answer)
        return answer

    def show_context(self):
        self.memory.print_context()

    def reset(self):
        self.chat_history = []
        self.memory.chat_history.clear()
