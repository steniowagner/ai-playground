from agent.generation.service import GenerationService
from agent.llm.base import LLMClient
from agent.retrieval.context_builder import ContextBuilder
from agent.retrieval.service import RetrievalService

from .cases import GENERATION_EVALUATION_CASES
from .evaluation import GenerationEvaluation
from .evaluator import GenerationEvaluator


class GenerationEvaluationService:
    def __init__(
        self,
        llm_client: LLMClient,
        context_builder: ContextBuilder,
        retrieval_service: RetrievalService,
    ) -> None:
        generation_service = GenerationService(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
            llm_client=llm_client,
        )
        self._evaluator = GenerationEvaluator(generation_service)

    def evaluate_generation(self) -> GenerationEvaluation:
        return [self._evaluator.evaluate(case) for case in GENERATION_EVALUATION_CASES]
