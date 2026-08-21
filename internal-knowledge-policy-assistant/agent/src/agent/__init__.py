from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline
from agent.repositories.factory import create_repository
from agent.services.knowledge_service import KnowledgeService
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
    knowledge_service = KnowledgeService(embedder=embedder, repository=repository)
    response = knowledge_service.search(query)

    for r in response:
        print(f"Score: {r.score}")
        print(f"File: {r.chunk.metadata['filename']}")
        print(f"Content: {r.chunk.content}")
        print("#######################")
