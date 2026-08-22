from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationEvaluationCase:
    question: str
    expected_facts: list[str]
    expected_sources: set[str]
    answerable: bool


GENERATION_EVALUATION_CASES = [
    GenerationEvaluationCase(
        question="Can contractors access production?",
        expected_facts=[
            "no standing production access",
            "read-only",
            "eight hours",
            "supervised",
        ],
        expected_sources={
            "contractor_access_policy.md",
        },
        answerable=True,
    ),
    GenerationEvaluationCase(
        question="Is alcohol reimbursable?",
        expected_facts=[
            "not reimbursable",
        ],
        expected_sources={
            "expense_policy.md",
        },
        answerable=True,
    ),
    GenerationEvaluationCase(
        question="What is the company parental leave policy?",
        expected_facts=[],
        expected_sources=set(),
        answerable=False,
    ),
]
