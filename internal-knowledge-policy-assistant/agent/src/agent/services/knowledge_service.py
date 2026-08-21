from agent.embeddings.base import Embedder
from agent.repositories.base import VectorRepository
from agent.repositories.search_result import SearchResult


class KnowledgeService:
    def __init__(self, embedder: Embedder, repository: VectorRepository) -> None:
        self._embedder = embedder
        self._repository = repository

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        query_emebedding = self._embedder.embed_query(query)
        return self._repository.search(query_emebedding, limit)
