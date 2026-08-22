from agent.domain.embedded_chunk import EmbeddedChunk
from agent.domain.search_result import SearchResult
from agent.utils.calculate_cosine_similarity import calculate_cosine_similarity

from .base import VectorRepository


class InMemoryVectorRepository(VectorRepository):
    def __init__(self):
        self._chunks: list[EmbeddedChunk] = []

    def add(self, chunks: list[EmbeddedChunk]) -> None:
        self._chunks.extend(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        results = [
            SearchResult(
                chunk=item.chunk,
                score=calculate_cosine_similarity(query_embedding, item.embedding),
            )
            for item in self._chunks
        ]

        if min_score > 0.0:
            results = [result for result in results if result.score >= min_score]

        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]
