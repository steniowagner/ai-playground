from agent.generation.answer import GenerationAnswer
from agent.generation.service import GenerationService
from agent.utils.default_values import DEFAULT_VALUES


class PolicyAssistant:
    def __init__(self, generation_service: GenerationService):
        self._generation_service = generation_service

    def ask(
        self,
        question: str,
        top_k: int = DEFAULT_VALUES["top_k"],
        min_score: float = DEFAULT_VALUES["min_score"],
    ) -> GenerationAnswer:
        return self._generation_service.answer(
            question=question, top_k=top_k, min_score=min_score
        )
