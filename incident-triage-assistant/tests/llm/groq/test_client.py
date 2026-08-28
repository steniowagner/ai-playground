from types import SimpleNamespace
from typing import Never

import groq
import httpx
import pytest
from incident_triage_assistant.llm.exceptions import LLMToolGenerationError
from incident_triage_assistant.llm.groq.client import GroqLLMClient
from incident_triage_assistant.llm.groq.messages_handler import GroqMessageHandler


class FailingCompletions:
    def __init__(self, error: groq.APIError) -> None:
        self.error = error

    def create(self, **_: object) -> Never:
        raise self.error


def client_with_error(error: groq.APIError) -> GroqLLMClient:
    client = object.__new__(GroqLLMClient)
    client._tools = []
    client._message_handler = GroqMessageHandler()
    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=FailingCompletions(error))
    )
    return client


def test_client_translates_and_chains_groq_error() -> None:
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    provider_error = groq.BadRequestError(
        "Tool generation failed",
        response=httpx.Response(400, request=request),
        body={"error": {"code": "tool_use_failed"}},
    )
    client = client_with_error(provider_error)

    with pytest.raises(LLMToolGenerationError) as raised:
        client.ask("Investigate INC-1042")

    assert raised.value.__cause__ is provider_error
    assert client._message_handler.messages == [
        {"role": "user", "content": "Investigate INC-1042"}
    ]
