from pathlib import Path

import pytest
from agent.domain.document import Document
from agent.ingestion.loaders.local import LocalDocumentLoader


def test_load_markdown_document(tmp_path: Path) -> None:
    document_path = tmp_path / "remote_work_policy.md"
    content = "# Remote Work\n\nEmployees need approval."
    document_path.write_text(content, encoding="utf-8")

    document = LocalDocumentLoader().load(str(document_path))

    assert isinstance(document, Document)
    assert document.id == "remote_work_policy"
    assert document.content == content
    assert document.source == str(document_path.resolve())
    assert document.type == ".md"
    assert document.metadata == {"filename": "remote_work_policy.md"}


def test_load_missing_document_is_rejected(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="Document not found"):
        LocalDocumentLoader().load(str(missing_path))


def test_load_unsupported_document_type_is_rejected(tmp_path: Path) -> None:
    document_path = tmp_path / "policy.txt"
    document_path.write_text("Policy content", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported Document extension: .txt"):
        LocalDocumentLoader().load(str(document_path))
