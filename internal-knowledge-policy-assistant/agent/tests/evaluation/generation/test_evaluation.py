import pytest
from agent.evaluation.generation.evaluation import GenerationEvaluation
from agent.generation.answer import GenerationAnswer


def make_evaluation(
    *,
    expected_facts: list[str] | None = None,
    facts_found: list[str] | None = None,
    sources_correct: bool = True,
    answerability_correct: bool = True,
) -> GenerationEvaluation:
    return GenerationEvaluation(
        question="question",
        answer=GenerationAnswer(content="answer", sources=["policy.md"]),
        expected_facts=expected_facts or [],
        expected_sources={"policy.md"},
        expected_answerable=True,
        facts_found=facts_found or [],
        sources_correct=sources_correct,
        answerability_correct=answerability_correct,
    )


def test_is_correct_when_all_checks_pass() -> None:
    evaluation = make_evaluation(
        expected_facts=["first fact", "second fact"],
        facts_found=["first fact", "second fact"],
    )

    assert evaluation.is_correct is True


@pytest.mark.parametrize(
    "evaluation",
    [
        make_evaluation(
            expected_facts=["first fact", "second fact"],
            facts_found=["first fact"],
        ),
        make_evaluation(sources_correct=False),
        make_evaluation(answerability_correct=False),
    ],
)
def test_is_incorrect_when_any_check_fails(
    evaluation: GenerationEvaluation,
) -> None:
    assert evaluation.is_correct is False


def test_unanswerable_case_can_be_correct_without_facts_or_sources() -> None:
    evaluation = GenerationEvaluation(
        question="Unknown policy?",
        answer=GenerationAnswer(content="No relevant information found.", sources=[]),
        expected_facts=[],
        expected_sources=set(),
        expected_answerable=False,
        facts_found=[],
        sources_correct=True,
        answerability_correct=True,
    )

    assert evaluation.is_correct is True
