from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import groq
import httpx
import pytest
from groq.types.chat import ChatCompletionMessage
from incident_triage_assistant.llm.exceptions import (
    LLMConfigurationError,
    LLMToolGenerationError,
)
from incident_triage_assistant.llm.groq.client import GroqLLMClient
from incident_triage_assistant.llm.groq.messages_handler import GroqMessageHandler
from incident_triage_assistant.llm.prompts import (
    CORRECTIVE_MESSAGE_PROMPT,
    DEFAULT_SYSTEM_PROMPT,
)


@pytest.fixture(autouse=True)
def groq_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_RETRY_COUNT", "2")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    monkeypatch.setenv("GROQ_TEMPERATURE", "0.2")


class SequencedCompletions:
    def __init__(self, *outcomes: Any) -> None:
        self._outcomes = iter(outcomes)
        self.call_count = 0
        self.requests: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.call_count += 1
        self.requests.append(deepcopy(kwargs))
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def provider_error(code: str) -> groq.BadRequestError:
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    return groq.BadRequestError(
        "Bad request",
        response=httpx.Response(400, request=request),
        body={"error": {"code": code}},
    )


def completion(content: str) -> SimpleNamespace:
    message = ChatCompletionMessage(role="assistant", content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def client_with_outcomes(*outcomes: Any) -> tuple[GroqLLMClient, SequencedCompletions]:
    completions = SequencedCompletions(*outcomes)
    client = object.__new__(GroqLLMClient)
    client._tools = []
    client._message_handler = GroqMessageHandler()
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_retries_tool_generation_error_once_then_returns_success() -> None:
    client, completions = client_with_outcomes(
        provider_error("tool_use_failed"),
        completion("Investigation complete"),
    )

    response = client.ask("Investigate INC-1042")

    assert completions.call_count == 2
    assert response.content == "Investigation complete"
    assert client._message_handler.messages == [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": "Investigate INC-1042"},
        {"role": "assistant", "content": "Investigation complete"},
    ]
    assert completions.requests[0]["messages"] == [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": "Investigate INC-1042"},
    ]
    assert completions.requests[1]["messages"][-1]["role"] == "user"
    assert len(client._message_handler.messages) == 3


def test_raises_after_tool_generation_retry_is_exhausted() -> None:
    first_error = provider_error("tool_use_failed")
    final_error = provider_error("tool_use_failed")
    client, completions = client_with_outcomes(first_error, final_error)

    with pytest.raises(LLMToolGenerationError) as raised:
        client.ask("Investigate INC-1042")

    assert completions.call_count == 2
    assert raised.value.__cause__ is final_error
    assert client._message_handler.messages == [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": "Investigate INC-1042"},
    ]


def test_does_not_retry_non_tool_generation_error() -> None:
    error = provider_error("invalid_request_error")
    client, completions = client_with_outcomes(error)

    with pytest.raises(LLMConfigurationError) as raised:
        client.ask("Investigate INC-1042")

    assert completions.call_count == 1
    assert raised.value.__cause__ is error


def test_invalid_result_feedback_is_persisted_before_continuing() -> None:
    client, completions = client_with_outcomes(completion("Corrected result"))

    response = client.continue_after_invalid_result("evidence is required")

    assert response.content == "Corrected result"
    corrective_message = client._message_handler.messages[-2]
    assert corrective_message["role"] == "user"
    assert CORRECTIVE_MESSAGE_PROMPT.strip() in corrective_message["content"]
    assert "evidence is required" in corrective_message["content"]
    assert completions.requests[0]["messages"][-1] == corrective_message
