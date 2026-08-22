from .evaluation import RetrievalEvaluation


def calculate_all_sources_hit(
    expected_sources: set[str],
    retrieved_sources: list[str],
    k: int,
) -> bool:
    top_k_sources = set(retrieved_sources[:k])

    return expected_sources.issubset(top_k_sources)


def calculate_hit_rate(evaluations: list[RetrievalEvaluation], k: int) -> float:
    if not evaluations:
        return 0.0

    hits = sum(
        calculate_all_sources_hit(
            expected_sources=evaluation.expected_sources,
            retrieved_sources=evaluation.retrieved_sources,
            k=k,
        )
        for evaluation in evaluations
    )

    return hits / len(evaluations)
