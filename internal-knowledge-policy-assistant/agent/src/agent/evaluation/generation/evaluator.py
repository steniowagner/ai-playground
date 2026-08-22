from agent.evaluation.generation.evaluation import GenerationEvaluation
from agent.generation.service import GenerationService

from .cases import GenerationEvaluationCase


class GenerationEvaluator:
    def __init__(self, generation_service: GenerationService):
        self._generation_service = generation_service

    def evaluate(self, case: GenerationEvaluationCase) -> GenerationEvaluation:
        answer = self._generation_service.answer(case.question)
        sources_correct = case.expected_sources.issubset(set(answer.sources))
        normalized_answer_content = answer.content.lower()
        actual_answerable = bool(answer.sources)

        facts_found = [
            fact
            for fact in case.expected_facts
            if fact.lower() in normalized_answer_content
        ]

        return GenerationEvaluation(
            question=case.question,
            answer=answer,
            expected_facts=case.expected_facts,
            expected_sources=case.expected_sources,
            expected_answerable=case.answerable,
            facts_found=facts_found,
            sources_correct=sources_correct,
            answerability_correct=(actual_answerable == case.answerable),
        )
