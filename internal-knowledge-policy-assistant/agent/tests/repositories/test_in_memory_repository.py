import pytest
from agent.domain.document_chunk import DocumentChunk
from agent.domain.embedded_chunk import EmbeddedChunk
from agent.repositories.in_memory import InMemoryVectorRepository


def make_embedded_chunk(
    chunk_id: str,
    embedding: list[float],
) -> EmbeddedChunk:
    return EmbeddedChunk(
        chunk=DocumentChunk(
            id=chunk_id,
            document_id="policy",
            content=f"Content for {chunk_id}",
            index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            token_count=3,
            start_char=0,
            end_char=10,
            metadata={"filename": "policy.md"},
        ),
        embedding=embedding,
    )


def test_empty_repository_returns_no_results() -> None:
    repository = InMemoryVectorRepository()

    assert repository.search([1.0, 0.0]) == []


def test_search_orders_chunks_by_descending_similarity() -> None:
    repository = InMemoryVectorRepository()
    repository.add(
        [
            make_embedded_chunk("policy:0", [0.0, 1.0]),
            make_embedded_chunk("policy:1", [1.0, 0.0]),
            make_embedded_chunk("policy:2", [-1.0, 0.0]),
        ]
    )

    results = repository.search([1.0, 0.0])

    assert [result.chunk.id for result in results] == [
        "policy:1",
        "policy:0",
        "policy:2",
    ]
    assert [result.score for result in results] == pytest.approx([1.0, 0.0, -1.0])


def test_search_respects_result_limit() -> None:
    repository = InMemoryVectorRepository()
    repository.add(
        [
            make_embedded_chunk("policy:0", [1.0, 0.0]),
            make_embedded_chunk("policy:1", [0.8, 0.2]),
            make_embedded_chunk("policy:2", [0.0, 1.0]),
        ]
    )

    results = repository.search([1.0, 0.0], top_k=2)

    assert len(results) == 2
    assert [result.chunk.id for result in results] == ["policy:0", "policy:1"]


def test_search_filters_scores_before_applying_top_k() -> None:
    repository = InMemoryVectorRepository()
    repository.add(
        [
            make_embedded_chunk("policy:0", [1.0, 0.0]),
            make_embedded_chunk("policy:1", [0.6, 0.8]),
            make_embedded_chunk("policy:2", [0.0, 1.0]),
        ]
    )

    results = repository.search(
        [1.0, 0.0],
        top_k=3,
        min_score=0.6,
    )

    assert [result.chunk.id for result in results] == ["policy:0", "policy:1"]
    assert [result.score for result in results] == pytest.approx([1.0, 0.6])


def test_add_appends_new_chunks() -> None:
    repository = InMemoryVectorRepository()
    repository.add([make_embedded_chunk("policy:0", [1.0, 0.0])])
    repository.add([make_embedded_chunk("policy:1", [0.0, 1.0])])

    results = repository.search([1.0, 0.0])

    assert {result.chunk.id for result in results} == {"policy:0", "policy:1"}


def test_search_rejects_mismatched_embedding_dimensions() -> None:
    repository = InMemoryVectorRepository()
    repository.add([make_embedded_chunk("policy:0", [1.0, 0.0])])

    with pytest.raises(ValueError, match="Embeddings dimensions must match"):
        repository.search([1.0, 0.0, 0.0])
