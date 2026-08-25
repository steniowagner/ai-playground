from typing import Literal

from .base import LLMClient
from .groq.client import GroqLLMClient

LLMProvider = Literal["groq"]


def create_llm_client(provider: LLMProvider) -> LLMClient:
    match provider:
        case "groq":
            return GroqLLMClient()
        case _:
            raise ValueError(f'Unknown LLM Provider "{provider}"')
