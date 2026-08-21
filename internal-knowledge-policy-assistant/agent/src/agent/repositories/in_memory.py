from agent.domain.embedded_chunk import EmbeddedChunk
from agent.vector_utils.calculate_cosine_similarity import calculate_cosine_similarity

from .base import VectorRepository
from .search_result import SearchResult


class InMemoryVectorRepository(VectorRepository):
    def __init__(self):
        self._chunks: list[EmbeddedChunk] = []

    def add(self, chunks: list[EmbeddedChunk]) -> None:
        self._chunks.extend(chunks)

    def search(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[SearchResult]:
        results = [
            SearchResult(
                chunk=item.chunk,
                score=calculate_cosine_similarity(query_embedding, item.embedding),
            )
            for item in self._chunks
        ]

        return sorted(results, key=lambda result: result.score, reverse=True)[:limit]
