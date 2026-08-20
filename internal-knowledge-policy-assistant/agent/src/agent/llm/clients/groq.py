from agent.llm.base import LLMClient
from groq import Groq


class GroqClient(LLMClient):
    def __init__(self) -> None:
        self._client = Groq()

    def ask(self, question: str) -> str:
        chat_completions = self._client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model="qwen/qwen3.6-27b",
        )
        return chat_completions.choices[0].message.content
