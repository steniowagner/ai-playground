from abc import ABC, abstractmethod

from agent.domain.embedded_chunk import EmbeddedChunk
from agent.domain.search_result import SearchResult


class VectorRepository(ABC):
    @abstractmethod
    def add(self, chunks: list[EmbeddedChunk]) -> None:
        pass

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        pass
