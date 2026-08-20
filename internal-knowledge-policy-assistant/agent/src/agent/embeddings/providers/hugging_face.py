from agent.embeddings.base import EmbeddingsProvider
from sentence_transformers import SentenceTransformer


class HuggingFaceEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self):
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self._model.encode_document(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )

        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._model.encode_document(
            [text], convert_to_numpy=True, normalize_embeddings=True
        )

        return embeddings[0].tolist()
