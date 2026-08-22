from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.generation.service import GenerationService
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline
from agent.llm.factory import create_llm_client
from agent.repositories.factory import create_repository
from agent.retrieval.context_builder import ContextBuilder
from agent.retrieval.service import RetrievalService
from agent.utils.ingest_local_files import ingest_local_files


def main() -> None:
    embedder = create_embedder("hugging-face")
    document_loader = create_document_loader("local")
    chunker = create_chunker("hugging-face")
    repository = create_repository("in-memory")

    ingestion_pipeline = IngestionPipeline(
        embedder=embedder,
        document_loader=document_loader,
        chunker=chunker,
        repository=repository,
    )

    ingest_local_files(ingestion_pipeline)

    retrieval_service = RetrievalService(embedder=embedder, repository=repository)
    llm_client = create_llm_client("groq")
    context_builder = ContextBuilder()
    generation_service = GenerationService(
        retrieval_service=retrieval_service,
        context_builder=context_builder,
        llm_client=llm_client,
    )

    question = "Can contractors access production?"
    answer = generation_service.answer(question)
    print(answer)
