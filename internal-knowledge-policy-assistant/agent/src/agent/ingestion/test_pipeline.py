import pytest

from agent.chunking.base import Chunk, Chunker
from agent.domain.document import Document
from agent.embeddings.base import Embedder
from agent.ingestion.loaders.base import DocumentLoader
from agent.ingestion.pipeline import IngestionPipeline


class FakeDocumentLoader(DocumentLoader):
    def __init__(self, document: Document) -> None:
        self.document = document
        self.sources: list[str] = []

    def load(self, source: str) -> Document:
        self.sources.append(source)
        return self.document


class FakeChunker(Chunker):
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.texts: list[str] = []

    def chunk(self, text: str) -> list[Chunk]:
        self.texts.append(text)
        return self.chunks


class FakeEmbedder(Embedder):
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = embeddings
        self.document_batches: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_batches.append(texts)
        return self.embeddings

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]


def make_pipeline(
    embeddings: list[list[float]],
) -> tuple[IngestionPipeline, FakeDocumentLoader, FakeChunker, FakeEmbedder]:
    document = Document(
        id="policy",
        content="First section. Second section.",
        source="/documents/policy.md",
        type=".md",
        metadata={"department": "HR"},
    )
    chunks = [
        Chunk("First section.", 0, 3, 0, 14),
        Chunk("Second section.", 1, 3, 15, 30),
    ]
    loader = FakeDocumentLoader(document)
    chunker = FakeChunker(chunks)
    embedder = FakeEmbedder(embeddings)

    return (
        IngestionPipeline(embedder, loader, chunker),
        loader,
        chunker,
        embedder,
    )


def test_ingest_loads_chunks_embeds_and_combines_results() -> None:
    pipeline, loader, chunker, embedder = make_pipeline(
        [[1.0, 0.0], [0.0, 1.0]]
    )

    result = pipeline.ingest("policy.md")

    assert loader.sources == ["policy.md"]
    assert chunker.texts == ["First section. Second section."]
    assert embedder.document_batches == [["First section.", "Second section."]]
    assert [item.chunk.id for item in result] == ["policy:0", "policy:1"]
    assert [item.embedding for item in result] == [
        [1.0, 0.0],
        [0.0, 1.0],
    ]
    assert result[0].chunk.metadata == {
        "department": "HR",
        "source": "/documents/policy.md",
        "document_type": ".md",
    }


def test_ingest_rejects_mismatched_embedding_count() -> None:
    pipeline, _, _, _ = make_pipeline([[1.0, 0.0]])

    with pytest.raises(ValueError, match=r"zip\(\) argument 2 is shorter"):
        pipeline.ingest("policy.md")
