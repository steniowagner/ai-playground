from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    question: str
    expected_sources: set[str]


RETRIEVAL_EVALUATION_CASES = [
    RetrievalEvaluationCase(
        question="Can contractors access production?",
        expected_sources={"contractor_access_policy.md"},
    ),
    RetrievalEvaluationCase(
        question="Is alcohol reimbursable?",
        expected_sources={"expense_policy.md"},
    ),
    RetrievalEvaluationCase(
        question="How much PTO can I carry into next year?",
        expected_sources={"pto_policy.md"},
    ),
    RetrievalEvaluationCase(
        question=(
            "Can contractors access production, and what production-access rules and approvals apply?"
        ),
        expected_sources={
            "contractor_access_policy.md",
            "production_access_policy.md",
        },
    ),
]
