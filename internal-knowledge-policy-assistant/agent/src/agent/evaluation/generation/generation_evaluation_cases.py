from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationEvaluationCase:
    question: str
    expected_facts: list[str]
    expected_sources: set[str]
    answerable: bool


GENERATION_EVALUATION_CASES = []
