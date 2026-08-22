from pathlib import Path

from agent.ingestion.parsers import pdf
from agent.ingestion.parsers.pdf import PDFParser


class FakePage:
    def __init__(self, text: str | None) -> None:
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class FakePdfReader:
    def __init__(self, document_path: Path) -> None:
        self.pages = [
            FakePage("  First page  "),
            FakePage(None),
            FakePage("   \n"),
            FakePage("Second page\ncontent"),
        ]


def test_parse_joins_non_empty_pdf_pages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.pdf"
    monkeypatch.setattr(pdf, "PdfReader", FakePdfReader)

    result = PDFParser().parse(document_path)

    assert result == "First page\n\nSecond page\ncontent"
