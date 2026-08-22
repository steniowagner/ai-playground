from agent.llm.base import LLMClient
from groq import Groq


class GroqClient(LLMClient):
    def __init__(self) -> None:
        self._client = Groq()

    def ask(self, question: str) -> str:
        chat_completions = self._client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
            reasoning_effort="none",
            max_completion_tokens=150,
            temperature=0.2,
        )
        return chat_completions.choices[0].message.content
