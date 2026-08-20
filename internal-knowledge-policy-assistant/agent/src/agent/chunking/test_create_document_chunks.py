from agent.chunking.base import Chunk
from agent.chunking.create_document_chunks import create_document_chunks
from agent.domain.document import Document


def test_create_document_chunks_enriches_raw_chunks() -> None:
    document = Document(
        id="remote-work",
        content="First policy section. Second policy section.",
        source="/documents/remote_work.md",
        type=".md",
        metadata={"department": "HR", "status": "current"},
    )
    chunks = [
        Chunk(
            content="First policy section.",
            index=0,
            token_count=4,
            start_char=0,
            end_char=21,
        ),
        Chunk(
            content="Second policy section.",
            index=1,
            token_count=4,
            start_char=22,
            end_char=44,
        ),
    ]

    result = create_document_chunks(document, chunks)

    assert [chunk.id for chunk in result] == ["remote-work:0", "remote-work:1"]
    assert all(chunk.document_id == document.id for chunk in result)
    assert [chunk.content for chunk in result] == [
        "First policy section.",
        "Second policy section.",
    ]
    assert result[0].index == 0
    assert result[0].token_count == 4
    assert result[0].start_char == 0
    assert result[0].end_char == 21
    assert result[0].metadata == {
        "department": "HR",
        "status": "current",
        "source": "/documents/remote_work.md",
        "document_type": ".md",
    }


def test_create_document_chunks_accepts_empty_chunk_list() -> None:
    document = Document(
        id="empty",
        content="",
        source="/documents/empty.md",
        type=".md",
    )

    assert create_document_chunks(document, []) == []
