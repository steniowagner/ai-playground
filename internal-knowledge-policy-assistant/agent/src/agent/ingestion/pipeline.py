from agent.chunking.base import Chunker
from agent.chunking.create_document_chunks import create_document_chunks
from agent.domain.embedded_chunk import EmbeddedChunk
from agent.embeddings.base import Embedder
from agent.ingestion.loaders.base import DocumentLoader
from agent.repositories.base import VectorRepository


class IngestionPipeline:
    def __init__(
        self,
        embedder: Embedder,
        document_loader: DocumentLoader,
        chunker: Chunker,
        repository: VectorRepository,
    ) -> None:
        self._document_loader = document_loader
        self._chunker = chunker
        self._embedder = embedder
        self._repository = repository

    def ingest(self, source: str) -> None:
        document = self._document_loader.load(source)
        raw_chunks = self._chunker.chunk(document.content)
        document_chunks = create_document_chunks(document, raw_chunks)

        embeddings = self._embedder.embed_documents(
            [document_chunk.content for document_chunk in document_chunks]
        )
        embedded_chunks = [
            EmbeddedChunk(chunk=chunk, embedding=vector)
            for chunk, vector in zip(document_chunks, embeddings, strict=True)
        ]

        self._repository.add(embedded_chunks)
