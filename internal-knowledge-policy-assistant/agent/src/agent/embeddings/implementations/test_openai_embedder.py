from types import SimpleNamespace

from agent.embeddings.implementations import openai
from agent.embeddings.implementations.openai import OpenAIEmbedder


class FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        inputs = kwargs["input"]

        if inputs == ["first", "second"]:
            return SimpleNamespace(
                data=[
                    SimpleNamespace(index=1, embedding=[0.0, 1.0]),
                    SimpleNamespace(index=0, embedding=[1.0, 0.0]),
                ]
            )

        return SimpleNamespace(
            data=[SimpleNamespace(index=0, embedding=[0.5, 0.5])]
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsResource()


def test_embed_documents_preserves_input_order(monkeypatch) -> None:
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    embedder = OpenAIEmbedder()

    result = embedder.embed_documents(["first", "second"])

    assert result == [[1.0, 0.0], [0.0, 1.0]]
    assert embedder._client.embeddings.calls == [
        {
            "model": "text-embedding-3-small",
            "input": ["first", "second"],
        }
    ]


def test_embed_documents_skips_api_for_empty_input(monkeypatch) -> None:
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    embedder = OpenAIEmbedder()

    assert embedder.embed_documents([]) == []
    assert embedder._client.embeddings.calls == []


def test_embed_query_returns_first_embedding(monkeypatch) -> None:
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    embedder = OpenAIEmbedder()

    result = embedder.embed_query("remote work")

    assert result == [0.5, 0.5]
    assert embedder._client.embeddings.calls == [
        {
            "model": "text-embedding-3-small",
            "input": ["remote work"],
        }
    ]
