import groq
from incident_triage_assistant.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMToolGenerationError,
    LLMUnavailableError,
)


def handle_groq_exception(error: groq.GroqError) -> Exception:
    if isinstance(error, groq.BadRequestError):
        body = error.body if isinstance(error.body, dict) else {}
        error_detail = body.get("error", {})
        provider_code = (
            error_detail.get("code") if isinstance(error_detail, dict) else None
        )

        if provider_code == "tool_use_failed":
            return LLMToolGenerationError()

        return LLMConfigurationError()

    if isinstance(
        error,
        (groq.AuthenticationError, groq.PermissionDeniedError),
    ):
        return LLMAuthenticationError()

    if isinstance(
        error,
        (groq.NotFoundError, groq.UnprocessableEntityError),
    ):
        return LLMConfigurationError()

    if isinstance(error, groq.RateLimitError):
        return LLMRateLimitError()

    if isinstance(
        error,
        (
            groq.APITimeoutError,
            groq.APIConnectionError,
            groq.ConflictError,
            groq.InternalServerError,
        ),
    ):
        return LLMUnavailableError()

    if isinstance(error, groq.APIResponseValidationError):
        return LLMInvalidResponseError()

    return LLMUnavailableError()
