import pytest

from agent.llm import factory


class FakeOpenAIClient:
    pass


class FakeGroqClient:
    pass


@pytest.mark.parametrize(
    ("provider", "attribute_name", "expected_type"),
    [
        ("openai", "OpenAIClient", FakeOpenAIClient),
        ("groq", "GroqClient", FakeGroqClient),
    ],
)
def test_create_llm_client(
    monkeypatch,
    provider: str,
    attribute_name: str,
    expected_type: type,
) -> None:
    monkeypatch.setattr(factory, attribute_name, expected_type)

    client = factory.create_llm_client(provider)  # type: ignore[arg-type]

    assert isinstance(client, expected_type)


def test_unsupported_llm_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported LLM provider: unknown"):
        factory.create_llm_client("unknown")  # type: ignore[arg-type]
