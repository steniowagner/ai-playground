from pathlib import Path

from agent.ingestion.parsers.base import DocumentParser


class MDParser(DocumentParser):
    def parse(self, document_path: Path) -> str:
        return document_path.read_text(encoding="utf-8")
