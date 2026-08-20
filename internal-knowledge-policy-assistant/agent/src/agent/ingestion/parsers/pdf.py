from pathlib import Path

from agent.ingestion.parsers.base import DocumentParser
from pypdf import PdfReader


class PDFParser(DocumentParser):
    def parse(self, document_path: Path) -> str:
        reader = PdfReader(document_path)
        pages_contents: list[str] = []

        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_contents.append(text.strip())

        return "\n\n".join(pages_contents)
