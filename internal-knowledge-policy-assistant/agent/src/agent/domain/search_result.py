from dataclasses import dataclass

from agent.domain.document_chunk import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float
