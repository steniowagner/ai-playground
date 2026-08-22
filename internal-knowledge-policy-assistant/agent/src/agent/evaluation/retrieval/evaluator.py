from agent.retrieval.service import RetrievalService

from .cases import RetrievalEvaluationCase
from .evaluation import RetrievalEvaluation


class RetrievalEvaluator:
    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval_service = retrieval_service

    def evaluate(self, case: RetrievalEvaluationCase) -> RetrievalEvaluation:
        retrieval_results = self._retrieval_service.search(query=case.question, top_k=5)

        retrieved_sources = [
            retrieval_result.chunk.metadata["filename"]
            for retrieval_result in retrieval_results
        ]

        retrieved_sources_set = set(retrieved_sources)

        return RetrievalEvaluation(
            question=case.question,
            retrieved_sources=retrieved_sources,
            expected_sources=case.expected_sources,
            is_correct=case.expected_sources.issubset(retrieved_sources_set),
        )
