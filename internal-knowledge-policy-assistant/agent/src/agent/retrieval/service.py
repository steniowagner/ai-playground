from agent.domain.search_result import SearchResult
from agent.embeddings.base import Embedder
from agent.repositories.base import VectorRepository


class RetrievalService:
    def __init__(self, embedder: Embedder, repository: VectorRepository) -> None:
        self._embedder = embedder
        self._repository = repository

    def _validate_search_numeric_params(
        self,
        top_k: int,
        min_score: float | None,
    ) -> None:
        if top_k <= 0:
            raise ValueError('"top_k" must be greater than zero')

        if min_score is not None and min_score < 0:
            raise ValueError('"min_score" must be greater than or equal to zero')

    def search(
        self, query: str, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:

        self._validate_search_numeric_params(top_k, min_score)

        query_embedding = self._embedder.embed_query(query)
        search_results = self._repository.search(
            query_embedding=query_embedding, top_k=top_k, min_score=min_score
        )

        return search_results
