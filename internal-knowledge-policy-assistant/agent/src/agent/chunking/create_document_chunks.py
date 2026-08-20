from agent.chunking.base import Chunk
from agent.domain.document import Document
from agent.domain.document_chunk import DocumentChunk


def create_document_chunks(
    document: Document, chunks: list[Chunk]
) -> list[DocumentChunk]:
    return [
        DocumentChunk(
            id=f"{document.id}:{chunk.index}",
            document_id=document.id,
            content=chunk.content,
            index=chunk.index,
            token_count=chunk.token_count,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            metadata={
                **document.metadata,
                "source": document.source,
                "document_type": document.type,
            },
        )
        for chunk in chunks
    ]
