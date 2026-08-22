import pytest
from agent.domain.document_chunk import DocumentChunk
from agent.domain.embedded_chunk import EmbeddedChunk
from agent.domain.search_result import SearchResult
from agent.embeddings.base import Embedder
from agent.repositories.base import VectorRepository
from agent.retrieval.service import RetrievalService


class FakeEmbedder(Embedder):
    def __init__(self, query_embedding: list[float]) -> None:
        self.query_embedding = query_embedding
        self.queries: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError("embed_documents() should not be called during retrieval")

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return self.query_embedding


class FakeRepository(VectorRepository):
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.search_calls: list[tuple[list[float], int, float]] = []

    def add(self, chunks: list[EmbeddedChunk]) -> None:
        raise AssertionError("add() should not be called during retrieval")

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        self.search_calls.append((query_embedding, top_k, min_score))
        return self.results


def make_result(score: float = 0.8) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id="policy:0",
            document_id="policy",
            content="Policy content",
            index=0,
            token_count=2,
            start_char=0,
            end_char=14,
            metadata={"filename": "policy.md"},
        ),
        score=score,
    )


def test_search_embeds_query_and_forwards_retrieval_parameters() -> None:
    expected_results = [make_result()]
    embedder = FakeEmbedder([1.0, 0.0])
    repository = FakeRepository(expected_results)
    service = RetrievalService(embedder=embedder, repository=repository)

    results = service.search(
        "Can contractors access production?",
        top_k=3,
        min_score=0.5,
    )

    assert results == expected_results
    assert embedder.queries == ["Can contractors access production?"]
    assert repository.search_calls == [([1.0, 0.0], 3, 0.5)]


def test_search_uses_default_parameters() -> None:
    embedder = FakeEmbedder([1.0, 0.0])
    repository = FakeRepository([])
    service = RetrievalService(embedder=embedder, repository=repository)

    assert service.search("query") == []
    assert repository.search_calls == [([1.0, 0.0], 5, 0.0)]


@pytest.mark.parametrize("top_k", [0, -1])
def test_search_rejects_non_positive_top_k(top_k: int) -> None:
    embedder = FakeEmbedder([1.0, 0.0])
    repository = FakeRepository([])
    service = RetrievalService(embedder=embedder, repository=repository)

    with pytest.raises(ValueError, match='"top_k" must be greater than zero'):
        service.search("query", top_k=top_k)

    assert embedder.queries == []
    assert repository.search_calls == []


def test_search_rejects_negative_min_score() -> None:
    embedder = FakeEmbedder([1.0, 0.0])
    repository = FakeRepository([])
    service = RetrievalService(embedder=embedder, repository=repository)

    with pytest.raises(
        ValueError,
        match='"min_score" must be greater than or equal to zero',
    ):
        service.search("query", min_score=-0.1)

    assert embedder.queries == []
    assert repository.search_calls == []
