from agent.domain.document_chunk import DocumentChunk
from agent.domain.search_result import SearchResult
from agent.retrieval.context_builder import ContextBuilder


def make_result(
    chunk_id: str,
    filename: str,
    content: str,
    score: float,
) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id=chunk_id,
            document_id="policy",
            content=content,
            index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            token_count=3,
            start_char=0,
            end_char=len(content),
            metadata={"filename": filename},
        ),
        score=score,
    )


def test_build_returns_empty_context_for_no_results() -> None:
    assert ContextBuilder().build([]) == ""


def test_build_formats_source_score_and_content() -> None:
    result = make_result(
        "policy:0",
        "policy.md",
        "Contractors require approval.",
        0.87654,
    )

    context = ContextBuilder().build([result])

    assert context == (
        "[Source: policy.md]\n"
        "[Score: 0.8765]\n"
        "Contractors require approval."
    )


def test_build_separates_multiple_results() -> None:
    results = [
        make_result("policy:0", "first.md", "First content", 0.9),
        make_result("policy:1", "second.md", "Second content", 0.7),
    ]

    context = ContextBuilder().build(results)

    assert context == (
        "[Source: first.md]\n"
        "[Score: 0.9000]\n"
        "First content\n\n---\n\n"
        "[Source: second.md]\n"
        "[Score: 0.7000]\n"
        "Second content"
    )
