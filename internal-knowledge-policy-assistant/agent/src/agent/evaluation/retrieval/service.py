from agent.embeddings.base import Embedder
from agent.evaluation.report import EvaluationReport
from agent.repositories.base import VectorRepository
from agent.retrieval.service import RetrievalService

from .build_report import build_retrieval_evaluation_report
from .cases import RETRIEVAL_EVALUATION_CASES
from .evaluator import RetrievalEvaluator


class RetrievalEvaluationService:
    def __init__(self, embedder: Embedder, repository: VectorRepository) -> None:
        self._retrieval_service = RetrievalService(
            embedder=embedder, repository=repository
        )

    def evaluate_retrieval(self) -> EvaluationReport:
        retrieval_evaluator = RetrievalEvaluator(self._retrieval_service)

        evaluation_results = [
            retrieval_evaluator.evaluate(case) for case in RETRIEVAL_EVALUATION_CASES
        ]

        report = build_retrieval_evaluation_report(evaluation_results)

        return report
