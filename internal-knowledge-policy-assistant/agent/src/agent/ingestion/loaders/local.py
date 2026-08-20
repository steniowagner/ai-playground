from pathlib import Path

from agent.domain.document import Document
from agent.ingestion.loaders.base import DocumentLoader
from agent.ingestion.parsers.factory import create_document_parser


class LocalDocumentLoader(DocumentLoader):
    def _check_is_valid_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            raise FileNotFoundError(f"Document not found: {file_path}")

    def load(self, source: str) -> Document:
        file_path = Path(source).expanduser().resolve()
        self._check_is_valid_file(file_path)

        document_parser = create_document_parser(file_path.suffix)
        content = document_parser.parse(file_path)

        return Document(
            id=file_path.stem,
            content=content,
            source=str(file_path),
            type=file_path.suffix,
            metadata={
                "filename": file_path.name,
            },
        )
