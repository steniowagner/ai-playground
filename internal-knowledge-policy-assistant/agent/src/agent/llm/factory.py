from typing import Literal

from .base import LLMClient
from .clients.groq import GroqClient
from .clients.openai import OpenAIClient


def create_llm_client(provider: Literal["openai"]) -> LLMClient:
    match provider:
        case "openai":
            return OpenAIClient()
        case "groq":
            return GroqClient()
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")
