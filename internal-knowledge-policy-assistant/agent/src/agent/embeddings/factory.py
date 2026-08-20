from typing import Literal

from agent.embeddings.base import Embedder
from agent.embeddings.implementations.hugging_face import (
    HuggingFaceEmbedder,
)
from agent.embeddings.implementations.openai import OpenAIEmbedder


def create_embedder(
    provider: Literal["hugging-face", "openai"],
) -> Embedder:
    match provider:
        case "hugging-face":
            return HuggingFaceEmbedder()
        case "openai":
            return OpenAIEmbedder()
        case _:
            raise ValueError(f"Unsupported Embedding provider: {provider}")
