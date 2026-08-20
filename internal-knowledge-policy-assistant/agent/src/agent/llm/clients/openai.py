from agent.llm.base import LLMClient
from openai import OpenAI


class OpenAIClient(LLMClient):
    def __init__(self) -> None:
        self._client = OpenAI()

    def ask(self, question: str) -> str:
        response = self._client.responses.create(
            model="gpt-5-nano",
            input=question,
        )
        return response.output_text
