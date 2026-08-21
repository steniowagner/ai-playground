from abc import ABC, abstractmethod

from agent.domain.embedded_chunk import EmbeddedChunk

from .search_result import SearchResult


class VectorRepository(ABC):
    @abstractmethod
    def add(self, chunks: list[EmbeddedChunk]) -> None:
        pass

    @abstractmethod
    def search(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[SearchResult]:
        pass
