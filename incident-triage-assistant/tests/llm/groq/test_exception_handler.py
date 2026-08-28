from collections.abc import Callable

import groq
import httpx
import pytest
from incident_triage_assistant.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMToolGenerationError,
    LLMUnavailableError,
)
from incident_triage_assistant.llm.groq.exception_handler import (
    handle_groq_exception,
)


def request() -> httpx.Request:
    return httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )


def response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=request())


def test_maps_failed_tool_generation_bad_request() -> None:
    error = groq.BadRequestError(
        "Tool generation failed",
        response=response(400),
        body={"error": {"code": "tool_use_failed"}},
    )

    translated = handle_groq_exception(error)

    assert isinstance(translated, LLMToolGenerationError)


@pytest.mark.parametrize(
    ("error_factory", "expected_type"),
    [
        (
            lambda: groq.BadRequestError(
                "Bad request",
                response=response(400),
                body={"error": {"code": "invalid_request_error"}},
            ),
            LLMConfigurationError,
        ),
        (
            lambda: groq.AuthenticationError(
                "Unauthorized", response=response(401), body=None
            ),
            LLMAuthenticationError,
        ),
        (
            lambda: groq.PermissionDeniedError(
                "Forbidden", response=response(403), body=None
            ),
            LLMAuthenticationError,
        ),
        (
            lambda: groq.NotFoundError(
                "Not found", response=response(404), body=None
            ),
            LLMConfigurationError,
        ),
        (
            lambda: groq.UnprocessableEntityError(
                "Invalid request", response=response(422), body=None
            ),
            LLMConfigurationError,
        ),
        (
            lambda: groq.RateLimitError(
                "Rate limited", response=response(429), body=None
            ),
            LLMRateLimitError,
        ),
        (
            lambda: groq.ConflictError(
                "Conflict", response=response(409), body=None
            ),
            LLMUnavailableError,
        ),
        (
            lambda: groq.InternalServerError(
                "Server error", response=response(500), body=None
            ),
            LLMUnavailableError,
        ),
        (
            lambda: groq.APITimeoutError(request()),
            LLMUnavailableError,
        ),
        (
            lambda: groq.APIConnectionError(request=request()),
            LLMUnavailableError,
        ),
        (
            lambda: groq.APIResponseValidationError(
                response=response(200), body={"unexpected": True}
            ),
            LLMInvalidResponseError,
        ),
        (
            lambda: groq.APIError(
                "Unknown API error", request(), body=None
            ),
            LLMUnavailableError,
        ),
    ],
)
def test_maps_groq_errors_to_internal_errors(
    error_factory: Callable[[], groq.GroqError],
    expected_type: type[Exception],
) -> None:
    translated = handle_groq_exception(error_factory())

    assert isinstance(translated, expected_type)
