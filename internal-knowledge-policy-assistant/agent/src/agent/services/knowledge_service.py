from agent.embeddings.base import Embedder
from agent.repositories.base import VectorRepository
from agent.repositories.search_result import SearchResult


class KnowledgeService:
    def __init__(self, embedder: Embedder, repository: VectorRepository) -> None:
        self._embedder = embedder
        self._repository = repository

    def search(
        self, query: str, top_k: int = 5, minimum_score: float | None = None
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        query_emebedding = self._embedder.embed_query(query)
        search_results = self._repository.search(query_emebedding, top_k)

        if minimum_score is not None:
            search_results = [
                search_result
                for search_result in search_results
                if search_result.score >= minimum_score
            ]

        return search_results
