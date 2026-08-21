import pytest
from agent.vector_utils.calculate_cosine_similarity import (
    calculate_cosine_similarity,
)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([1.0, 2.0], [1.0, 2.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
        ([2.0, 0.0], [4.0, 0.0], 1.0),
    ],
)
def test_calculate_cosine_similarity(
    left: list[float],
    right: list[float],
    expected: float,
) -> None:
    assert calculate_cosine_similarity(left, right) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ([0.0, 0.0], [1.0, 0.0]),
        ([1.0, 0.0], [0.0, 0.0]),
        ([], []),
    ],
)
def test_zero_length_vector_returns_zero(
    left: list[float],
    right: list[float],
) -> None:
    assert calculate_cosine_similarity(left, right) == 0.0


def test_mismatched_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError, match="Embeddings dimensions must match"):
        calculate_cosine_similarity([1.0, 0.0], [1.0])
