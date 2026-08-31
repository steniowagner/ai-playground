class LLMError(Exception):
    pass


class LLMToolGenerationError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The language model produced an invalid tool request and the investigation could not continue. Please try again."
        )


class LLMRateLimitError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The language-model service is receiving too many requests. Please wait a moment and try again."
        )


class LLMAuthenticationError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The application could not authenticate with the language-model service. Please check the provider credentials."
        )


class LLMConfigurationError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The language-model request could not be completed because the provider configuration is invalid."
        )


class LLMUnavailableError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The language-model service is temporarily unavailable. Please try again later."
        )


class LLMInvalidResponseError(LLMError):
    def __init__(self) -> None:
        super().__init__(
            "The language-model service returned an invalid response. Please try again."
        )
