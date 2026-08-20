from typing import Literal

from agent.ingestion.parsers.base import DocumentParser
from agent.ingestion.parsers.md import MDParser
from agent.ingestion.parsers.pdf import PDFParser


def create_document_parser(file_extension: Literal[".pdf", ".md"]) -> DocumentParser:
    match file_extension:
        case ".md":
            return MDParser()
        case ".pdf":
            return PDFParser()
        case _:
            raise ValueError(f"Unsupported Document extension: {file_extension}")
