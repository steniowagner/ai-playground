import pytest
from agent.embeddings import factory


class FakeHuggingFaceEmbedder:
    pass


class FakeOpenAIEmbedder:
    pass


@pytest.mark.parametrize(
    ("provider", "attribute_name", "expected_type"),
    [
        ("hugging-face", "HuggingFaceEmbedder", FakeHuggingFaceEmbedder),
        ("openai", "OpenAIEmbedder", FakeOpenAIEmbedder),
    ],
)
def test_create_embedder(
    monkeypatch,
    provider: str,
    attribute_name: str,
    expected_type: type,
) -> None:
    monkeypatch.setattr(factory, attribute_name, expected_type)

    result = factory.create_embedder(provider)  # type: ignore[arg-type]

    assert isinstance(result, expected_type)


def test_unsupported_embedding_provider_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported Embedding provider: unknown",
    ):
        factory.create_embedder("unknown")  # type: ignore[arg-type]
