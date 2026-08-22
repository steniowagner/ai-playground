import pytest
from agent.ingestion.loaders.factory import create_document_loader
from agent.ingestion.loaders.local import LocalDocumentLoader


def test_create_local_document_loader() -> None:
    loader = create_document_loader("local")

    assert isinstance(loader, LocalDocumentLoader)


def test_unsupported_document_loader_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported Document loader: remote"):
        create_document_loader("remote")  # type: ignore[arg-type]
