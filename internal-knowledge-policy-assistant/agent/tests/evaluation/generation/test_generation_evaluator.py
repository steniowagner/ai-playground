from agent.evaluation.generation.cases import (
    GenerationEvaluationCase,
)
from agent.evaluation.generation.evaluator import GenerationEvaluator
from agent.generation.answer import GenerationAnswer


class FakeGenerationService:
    def __init__(self, answer: GenerationAnswer) -> None:
        self.answer_value = answer
        self.questions: list[str] = []

    def answer(self, question: str) -> GenerationAnswer:
        self.questions.append(question)
        return self.answer_value


def test_evaluate_finds_facts_case_insensitively() -> None:
    service = FakeGenerationService(
        GenerationAnswer(
            content=(
                "Contractors have NO STANDING PRODUCTION ACCESS. "
                "Exceptional access is read-only and supervised."
            ),
            sources=["contractor.md"],
        )
    )
    evaluator = GenerationEvaluator(service)  # type: ignore[arg-type]
    case = GenerationEvaluationCase(
        question="Can contractors access production?",
        expected_facts=[
            "no standing production access",
            "read-only",
            "supervised",
        ],
        expected_sources={"contractor.md"},
        answerable=True,
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.facts_found == case.expected_facts
    assert evaluation.sources_correct is True
    assert evaluation.answerability_correct is True
    assert evaluation.is_correct is True
    assert service.questions == [case.question]


def test_evaluate_detects_missing_fact() -> None:
    service = FakeGenerationService(
        GenerationAnswer(
            content="Contractor access is read-only.",
            sources=["contractor.md"],
        )
    )
    evaluator = GenerationEvaluator(service)  # type: ignore[arg-type]
    case = GenerationEvaluationCase(
        question="Can contractors access production?",
        expected_facts=["read-only", "supervised"],
        expected_sources={"contractor.md"},
        answerable=True,
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.facts_found == ["read-only"]
    assert evaluation.is_correct is False


def test_evaluate_detects_missing_required_source() -> None:
    service = FakeGenerationService(
        GenerationAnswer(
            content="Contractor access is read-only.",
            sources=["production.md"],
        )
    )
    evaluator = GenerationEvaluator(service)  # type: ignore[arg-type]
    case = GenerationEvaluationCase(
        question="Can contractors access production?",
        expected_facts=["read-only"],
        expected_sources={"contractor.md", "production.md"},
        answerable=True,
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.sources_correct is False
    assert evaluation.is_correct is False


def test_evaluate_accepts_correct_refusal() -> None:
    service = FakeGenerationService(
        GenerationAnswer(
            content="I could not find relevant information.",
            sources=[],
        )
    )
    evaluator = GenerationEvaluator(service)  # type: ignore[arg-type]
    case = GenerationEvaluationCase(
        question="What is the parental leave policy?",
        expected_facts=[],
        expected_sources=set(),
        answerable=False,
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.answerability_correct is True
    assert evaluation.sources_correct is True
    assert evaluation.is_correct is True


def test_evaluate_rejects_sourced_answer_for_unanswerable_case() -> None:
    service = FakeGenerationService(
        GenerationAnswer(
            content="The policy provides twelve weeks.",
            sources=["unrelated.md"],
        )
    )
    evaluator = GenerationEvaluator(service)  # type: ignore[arg-type]
    case = GenerationEvaluationCase(
        question="What is the parental leave policy?",
        expected_facts=[],
        expected_sources=set(),
        answerable=False,
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.answerability_correct is False
    assert evaluation.is_correct is False
