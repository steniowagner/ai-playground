from agent.domain.document_chunk import DocumentChunk
from agent.domain.search_result import SearchResult
from agent.evaluation.retrieval.evaluation_cases import RetrievalEvaluationCase
from agent.evaluation.retrieval.evaluator import RetrievalEvaluator


class FakeRetrievalService:
    def __init__(self, filenames: list[str]) -> None:
        self.filenames = filenames
        self.search_calls: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int = 5):
        self.search_calls.append((query, top_k))
        return [
            SearchResult(
                chunk=DocumentChunk(
                    id=f"chunk:{index}",
                    document_id=filename,
                    content="content",
                    index=index,
                    token_count=1,
                    start_char=0,
                    end_char=7,
                    metadata={"filename": filename},
                ),
                score=1.0 - (index * 0.1),
            )
            for index, filename in enumerate(self.filenames)
        ]


def test_evaluate_marks_single_source_case_correct() -> None:
    retrieval_service = FakeRetrievalService(["policy.md", "other.md"])
    evaluator = RetrievalEvaluator(retrieval_service)  # type: ignore[arg-type]
    case = RetrievalEvaluationCase(
        question="Policy question",
        expected_sources={"policy.md"},
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.is_correct is True
    assert evaluation.retrieved_sources == ["policy.md", "other.md"]
    assert retrieval_service.search_calls == [("Policy question", 5)]


def test_evaluate_marks_multi_source_case_correct_when_all_sources_exist() -> None:
    retrieval_service = FakeRetrievalService(
        ["contractor.md", "other.md", "production.md"]
    )
    evaluator = RetrievalEvaluator(retrieval_service)  # type: ignore[arg-type]
    case = RetrievalEvaluationCase(
        question="Contractor production rules",
        expected_sources={"contractor.md", "production.md"},
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.is_correct is True


def test_evaluate_marks_multi_source_case_incorrect_when_one_source_is_missing() -> (
    None
):
    retrieval_service = FakeRetrievalService(["contractor.md", "other.md"])
    evaluator = RetrievalEvaluator(retrieval_service)  # type: ignore[arg-type]
    case = RetrievalEvaluationCase(
        question="Contractor production rules",
        expected_sources={"contractor.md", "production.md"},
    )

    evaluation = evaluator.evaluate(case)

    assert evaluation.is_correct is False
