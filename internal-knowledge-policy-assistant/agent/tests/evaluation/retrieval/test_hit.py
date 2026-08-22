import pytest
from agent.evaluation.retrieval.evaluation import RetrievalEvaluation
from agent.evaluation.retrieval.hit import (
    calculate_all_sources_hit,
    calculate_hit_rate,
)


def make_evaluation(
    expected_sources: set[str],
    retrieved_sources: list[str],
) -> RetrievalEvaluation:
    return RetrievalEvaluation(
        question="question",
        expected_sources=expected_sources,
        retrieved_sources=retrieved_sources,
        is_correct=expected_sources.issubset(set(retrieved_sources)),
    )


def test_single_source_hit_when_source_is_inside_top_k() -> None:
    assert calculate_all_sources_hit(
        expected_sources={"policy.md"},
        retrieved_sources=["other.md", "policy.md", "third.md"],
        k=2,
    )


def test_single_source_miss_when_source_is_below_top_k() -> None:
    assert not calculate_all_sources_hit(
        expected_sources={"policy.md"},
        retrieved_sources=["other.md", "second.md", "policy.md"],
        k=2,
    )


def test_multi_source_hit_requires_every_source_inside_top_k() -> None:
    assert calculate_all_sources_hit(
        expected_sources={"contractor.md", "production.md"},
        retrieved_sources=["contractor.md", "other.md", "production.md"],
        k=3,
    )


def test_multi_source_miss_when_one_source_is_missing() -> None:
    assert not calculate_all_sources_hit(
        expected_sources={"contractor.md", "production.md"},
        retrieved_sources=["contractor.md", "other.md", "security.md"],
        k=3,
    )


def test_calculate_hit_rate_averages_case_results() -> None:
    evaluations = [
        make_evaluation({"first.md"}, ["first.md"]),
        make_evaluation({"second.md"}, ["other.md", "second.md"]),
        make_evaluation({"missing.md"}, ["other.md"]),
        make_evaluation(
            {"contractor.md", "production.md"},
            ["contractor.md", "production.md"],
        ),
    ]

    assert calculate_hit_rate(evaluations, k=1) == pytest.approx(0.25)
    assert calculate_hit_rate(evaluations, k=2) == pytest.approx(0.75)


def test_calculate_hit_rate_returns_zero_for_no_evaluations() -> None:
    assert calculate_hit_rate([], k=5) == 0.0
