from dataclasses import dataclass

from agent.domain.document_chunk import DocumentChunk


@dataclass
class EmbeddedChunk:
    chunk: DocumentChunk
    embedding: list[float]
