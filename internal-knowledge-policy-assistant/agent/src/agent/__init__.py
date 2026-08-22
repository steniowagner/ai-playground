from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline
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

    query = "Can contractors access production?"
    retrieval_service = RetrievalService(embedder=embedder, repository=repository)
    search_results = retrieval_service.search(query=query)
    context_builder = ContextBuilder()
    context = context_builder.build(search_results)

    for r in search_results:
        print(f"Score: {r.score}")
        print(f"File: {r.chunk.metadata['filename']}")
        print(f"Content: {r.chunk.content}")
        print("#######################")

    print("#######################")

    print(f"Context: {context}")
