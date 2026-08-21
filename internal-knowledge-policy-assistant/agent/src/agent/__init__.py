from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline
from agent.repositories.factory import create_repository


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

    ingestion_pipeline.ingest(
        "/Users/steniowagner/dev/agents-playground/internal-knowledge-policy-assistant/agent/src/agent/documents/pdf/expense_policy.pdf"
    )

    query = "is alchol reimbursable?"
    query_emebedding = embedder.embed_query(query)

    d = repository.search(query_embedding=query_emebedding)
    for r in d:
        print(f"Score: {r.score}")
        print(f"File: {r.chunk.metadata['filename']}")
        print(f"Content: {r.chunk.content}")
        print("#######################")
