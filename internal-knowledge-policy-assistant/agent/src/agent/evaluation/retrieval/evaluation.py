from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalEvaluation:
    question: str
    retrieved_sources: list[str]
    expected_sources: set[str]
    is_correct: bool
