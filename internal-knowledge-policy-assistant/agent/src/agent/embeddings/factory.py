from typing import Literal

from agent.embeddings.base import EmbeddingsProvider
from agent.embeddings.providers.hugging_face import (
    HuggingFaceEmbeddingsProvider,
)
from agent.embeddings.providers.openai import OpenAIEmbeddingsProvider


def create_embeddings_provider(
    provider: Literal["hugging-face", "openai"],
) -> EmbeddingsProvider:
    match provider:
        case "hugging-face":
            return HuggingFaceEmbeddingsProvider()
        case "openai":
            return OpenAIEmbeddingsProvider()
        case _:
            raise ValueError(f"Unsupported Embedding provider: {provider}")
