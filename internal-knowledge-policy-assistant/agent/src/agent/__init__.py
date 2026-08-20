from agent.chunking import create_chunker
from agent.embeddings.factory import create_embedder
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.pipeline import IngestionPipeline


def main() -> None:
    hugging_face_embedder = create_embedder("hugging-face")
    local_document_loader = create_document_loader("local")
    hugging_face_chunker = create_chunker("hugging-face")

    ingestion_pipeline = IngestionPipeline(
        embedder=hugging_face_embedder,
        document_loader=local_document_loader,
        chunker=hugging_face_chunker,
    )

    d = ingestion_pipeline.ingest(
        "/Users/steniowagner/dev/agents-playground/internal-knowledge-policy-assistant/agent/src/agent/documents/pdf/expense_policy.pdf"
    )

    print(d)
