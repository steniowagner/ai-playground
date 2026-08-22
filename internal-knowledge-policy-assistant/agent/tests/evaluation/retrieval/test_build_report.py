import pytest
from agent.evaluation.report import EvaluationReport
from agent.evaluation.retrieval.build_report import (
    build_retrieval_evaluation_report,
)
from agent.evaluation.retrieval.evaluation import RetrievalEvaluation


def make_evaluation(
    expected_source: str,
    retrieved_sources: list[str],
) -> RetrievalEvaluation:
    return RetrievalEvaluation(
        question="question",
        retrieved_sources=retrieved_sources,
        expected_sources={expected_source},
        is_correct=expected_source in retrieved_sources,
    )


def test_build_report_calculates_hit_rates() -> None:
    evaluations = [
        make_evaluation("first.md", ["first.md"]),
        make_evaluation("second.md", ["other.md", "second.md"]),
        make_evaluation(
            "third.md",
            ["one.md", "two.md", "three.md", "third.md"],
        ),
        make_evaluation("missing.md", ["other.md"]),
    ]

    report = build_retrieval_evaluation_report(evaluations)

    assert report.total_cases == 4
    assert report.hit_at_1 == pytest.approx(0.25)
    assert report.hit_at_3 == pytest.approx(0.5)
    assert report.hit_at_5 == pytest.approx(0.75)


def test_build_report_accepts_empty_evaluation_list() -> None:
    assert build_retrieval_evaluation_report([]) == EvaluationReport(
        total_cases=0,
        hit_at_1=0.0,
        hit_at_3=0.0,
        hit_at_5=0.0,
    )
