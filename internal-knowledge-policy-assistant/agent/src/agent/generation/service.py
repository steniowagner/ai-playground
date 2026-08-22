from agent.llm.base import LLMClient
from agent.retrieval.context_builder import ContextBuilder
from agent.retrieval.service import RetrievalService

from .answer import GenerationAnswer
from .prompt_builder import build_rag_prompt


class GenerationService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_builder: ContextBuilder,
        llm_client: LLMClient,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._context_builder = context_builder
        self._llm_client = llm_client

    def answer(
        self,
        question: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> GenerationAnswer:
        search_results = self._retrieval_service.search(
            query=question, top_k=top_k, min_score=min_score
        )

        if not search_results:
            return GenerationAnswer(
                content="I could not find relevant information in the knowledge base.",
                sources=[],
            )

        context = self._context_builder.build(search_results)
        prompt = build_rag_prompt(question, context)
        llm_response = self._llm_client.ask(prompt)
        sources = list(
            dict.fromkeys(
                search_result.chunk.metadata["filename"]
                for search_result in search_results
            )
        )

        return GenerationAnswer(content=llm_response, sources=sources)
