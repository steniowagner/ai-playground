from agent.domain.document_chunk import DocumentChunk
from agent.domain.search_result import SearchResult
from agent.generation.answer import GenerationAnswer
from agent.generation.service import GenerationService
from agent.llm.base import LLMClient


class FakeRetrievalService:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.search_calls: list[tuple[str, int, float]] = []

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        self.search_calls.append((query, top_k, min_score))
        return self.results


class FakeContextBuilder:
    def __init__(self, context: str) -> None:
        self.context = context
        self.calls: list[list[SearchResult]] = []

    def build(self, results: list[SearchResult]) -> str:
        self.calls.append(results)
        return self.context


class FakeLLMClient(LLMClient):
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def ask(self, question: str) -> str:
        self.prompts.append(question)
        return self.response


def make_result(
    chunk_id: str,
    filename: str,
    score: float,
) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id=chunk_id,
            document_id=filename,
            content=f"Content from {filename}",
            index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            token_count=3,
            start_char=0,
            end_char=20,
            metadata={"filename": filename},
        ),
        score=score,
    )


def test_answer_returns_unsupported_response_without_calling_llm() -> None:
    retrieval_service = FakeRetrievalService([])
    context_builder = FakeContextBuilder("unused")
    llm_client = FakeLLMClient("unused")
    service = GenerationService(
        retrieval_service=retrieval_service,  # type: ignore[arg-type]
        context_builder=context_builder,  # type: ignore[arg-type]
        llm_client=llm_client,
    )

    answer = service.answer("Unknown policy?", top_k=3, min_score=0.6)

    assert answer == GenerationAnswer(
        content="I could not find relevant information in the knowledge base.",
        sources=[],
    )
    assert retrieval_service.search_calls == [("Unknown policy?", 3, 0.6)]
    assert context_builder.calls == []
    assert llm_client.prompts == []


def test_answer_builds_grounded_prompt_and_returns_unique_sources() -> None:
    results = [
        make_result("contractor:0", "contractor.md", 0.9),
        make_result("production:1", "production.md", 0.8),
        make_result("contractor:2", "contractor.md", 0.7),
    ]
    retrieval_service = FakeRetrievalService(results)
    context_builder = FakeContextBuilder("Retrieved policy context")
    llm_client = FakeLLMClient("Contractors require approval.")
    service = GenerationService(
        retrieval_service=retrieval_service,  # type: ignore[arg-type]
        context_builder=context_builder,  # type: ignore[arg-type]
        llm_client=llm_client,
    )

    answer = service.answer(
        "Can contractors access production?",
        top_k=4,
        min_score=0.5,
    )

    assert answer == GenerationAnswer(
        content="Contractors require approval.",
        sources=["contractor.md", "production.md"],
    )
    assert retrieval_service.search_calls == [
        ("Can contractors access production?", 4, 0.5)
    ]
    assert context_builder.calls == [results]
    assert len(llm_client.prompts) == 1
    assert "Retrieved policy context" in llm_client.prompts[0]
    assert "Can contractors access production?" in llm_client.prompts[0]
    assert "using only the supplied context" in llm_client.prompts[0]
