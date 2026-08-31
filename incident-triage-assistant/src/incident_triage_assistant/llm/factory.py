from typing import Literal

from incident_triage_assistant.tools.tools_registry import ToolRegistration

from .base import LLMClient
from .groq.client import GroqLLMClient

LLMProvider = Literal["groq"]


def create_llm_client(
    provider: LLMProvider, tools_definitions: list[ToolRegistration]
) -> LLMClient:
    match provider:
        case "groq":
            return GroqLLMClient(tools_definitions=tools_definitions)
        case _:
            raise ValueError(f'Unknown LLM Provider "{provider}"')
