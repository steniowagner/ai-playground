import pytest
from agent.chunking.implementations.hugging_face import HuggingFaceFixedSizeChunker


@pytest.fixture(scope="module")
def chunker() -> HuggingFaceFixedSizeChunker:
    return HuggingFaceFixedSizeChunker(
        chunk_size=5,
        chunk_overlap=2,
    )


def test_empty_text_returns_no_chunks(
    chunker: HuggingFaceFixedSizeChunker,
) -> None:
    assert chunker.chunk("") == []
    assert chunker.chunk("   ") == []
    assert chunker.chunk("\n\n") == []


def test_small_document_creates_one_chunk() -> None:
    chunker = HuggingFaceFixedSizeChunker(
        chunk_size=256,
        chunk_overlap=32,
    )

    text = "Employees need approval before accessing production."

    chunks = chunker.chunk(text)

    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content == text
    assert chunks[0].token_count <= 256
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)


def test_chunks_do_not_exceed_size(
    chunker: HuggingFaceFixedSizeChunker,
) -> None:
    text = (
        "Employees must request approval before receiving production "
        "database access from the information security team."
    )

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    assert all(chunk.token_count <= 5 for chunk in chunks)


def test_chunk_positions_match_original_text(
    chunker: HuggingFaceFixedSizeChunker,
) -> None:
    text = "Employees must request approval before receiving production access."

    for chunk in chunker.chunk(text):
        assert chunk.content == text[chunk.start_char : chunk.end_char]


def test_consecutive_chunks_overlap(
    chunker: HuggingFaceFixedSizeChunker,
) -> None:
    text = (
        "Employees must request approval before receiving production "
        "database access from the information security team."
    )

    chunks = chunker.chunk(text)

    for previous, current in zip(chunks, chunks[1:]):
        assert current.start_char < previous.end_char


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (10, -1),
        (10, 10),
        (10, 11),
    ],
)
def test_invalid_configuration_is_rejected(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    with pytest.raises(ValueError):
        HuggingFaceFixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
