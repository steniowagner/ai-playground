from agent.embeddings.base import EmbeddingsProvider
from openai import OpenAI


class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self):
        self._client = OpenAI()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embeddings.create(
            model="text-embedding-3-small", input=texts
        )

        ordered_embeddings = sorted(response.data, key=lambda item: item.index)

        return [item.embedding for item in ordered_embeddings]

    def embed_query(self, text) -> list[float]:
        response = self._client.embeddings.create(
            model="text-embedding-3-small", input=[text]
        )

        return response.data[0].embedding
