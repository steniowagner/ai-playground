import pytest
from agent.ingestion.parsers.factory import create_document_parser
from agent.ingestion.parsers.md import MDParser
from agent.ingestion.parsers.pdf import PDFParser


@pytest.mark.parametrize(
    ("file_extension", "expected_parser_type"),
    [
        (".md", MDParser),
        (".pdf", PDFParser),
    ],
)
def test_create_document_parser(
    file_extension: str, expected_parser_type: type
) -> None:
    parser = create_document_parser(file_extension)  # type: ignore[arg-type]

    assert isinstance(parser, expected_parser_type)


def test_unsupported_document_parser_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported Document extension: .txt"):
        create_document_parser(".txt")  # type: ignore[arg-type]
