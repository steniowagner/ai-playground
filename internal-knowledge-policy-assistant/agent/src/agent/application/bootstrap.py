from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.generation.service import GenerationService
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline
from agent.llm.factory import create_llm_client
from agent.repositories.factory import create_repository
from agent.retrieval.context_builder import ContextBuilder
from agent.retrieval.service import RetrievalService
from agent.utils.default_values import DEFAULT_VALUES
from agent.utils.ingest_local_files import ingest_local_files

from .assistant import PolicyAssistant


def create_policy_assistant() -> PolicyAssistant:
    document_loader = create_document_loader(DEFAULT_VALUES["loader"])
    embedder = create_embedder(DEFAULT_VALUES["embedder"])
    chunker = create_chunker(DEFAULT_VALUES["chunker"])
    repository = create_repository(DEFAULT_VALUES["repository"])

    ingestion_pipeline = IngestionPipeline(
        document_loader=document_loader,
        embedder=embedder,
        chunker=chunker,
        repository=repository,
    )

    ingest_local_files(ingestion_pipeline)

    retrieval_service = RetrievalService(
        embedder=embedder,
        repository=repository,
    )

    generation_service = GenerationService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        llm_client=create_llm_client("groq"),
    )

    return PolicyAssistant(generation_service)
