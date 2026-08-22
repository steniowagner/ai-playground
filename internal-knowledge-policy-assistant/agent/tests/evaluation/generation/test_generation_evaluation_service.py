from agent.evaluation.generation import service as service_module
from agent.evaluation.generation.cases import (
    GenerationEvaluationCase,
)
from agent.evaluation.generation.evaluation import GenerationEvaluation
from agent.evaluation.generation.service import GenerationEvaluationService
from agent.generation.answer import GenerationAnswer


class FakeGenerationService:
    def __init__(self, retrieval_service, context_builder, llm_client) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.llm_client = llm_client


class FakeGenerationEvaluator:
    instances: list["FakeGenerationEvaluator"] = []

    def __init__(self, generation_service) -> None:
        self.generation_service = generation_service
        self.cases: list[GenerationEvaluationCase] = []
        self.__class__.instances.append(self)

    def evaluate(self, case: GenerationEvaluationCase) -> GenerationEvaluation:
        self.cases.append(case)
        return GenerationEvaluation(
            question=case.question,
            answer=GenerationAnswer(
                content="answer",
                sources=list(case.expected_sources),
            ),
            expected_facts=case.expected_facts,
            expected_sources=case.expected_sources,
            expected_answerable=case.answerable,
            facts_found=case.expected_facts,
            sources_correct=True,
            answerability_correct=True,
        )


def test_evaluate_generation_evaluates_every_configured_case(
    monkeypatch,
) -> None:
    cases = [
        GenerationEvaluationCase(
            question="first question",
            expected_facts=["first fact"],
            expected_sources={"first.md"},
            answerable=True,
        ),
        GenerationEvaluationCase(
            question="second question",
            expected_facts=[],
            expected_sources=set(),
            answerable=False,
        ),
    ]
    FakeGenerationEvaluator.instances = []
    monkeypatch.setattr(service_module, "GENERATION_EVALUATION_CASES", cases)
    monkeypatch.setattr(
        service_module,
        "GenerationService",
        FakeGenerationService,
    )
    monkeypatch.setattr(
        service_module,
        "GenerationEvaluator",
        FakeGenerationEvaluator,
    )

    service = GenerationEvaluationService(
        llm_client=object(),  # type: ignore[arg-type]
        context_builder=object(),  # type: ignore[arg-type]
        retrieval_service=object(),  # type: ignore[arg-type]
    )
    results = service.evaluate_generation()

    assert len(results) == 2
    assert [result.question for result in results] == [
        "first question",
        "second question",
    ]
    assert len(FakeGenerationEvaluator.instances) == 1
    assert FakeGenerationEvaluator.instances[0].cases == cases


def test_evaluate_generation_accepts_no_cases(monkeypatch) -> None:
    FakeGenerationEvaluator.instances = []
    monkeypatch.setattr(service_module, "GENERATION_EVALUATION_CASES", [])
    monkeypatch.setattr(
        service_module,
        "GenerationService",
        FakeGenerationService,
    )
    monkeypatch.setattr(
        service_module,
        "GenerationEvaluator",
        FakeGenerationEvaluator,
    )
    service = GenerationEvaluationService(
        llm_client=object(),  # type: ignore[arg-type]
        context_builder=object(),  # type: ignore[arg-type]
        retrieval_service=object(),  # type: ignore[arg-type]
    )

    assert service.evaluate_generation() == []
