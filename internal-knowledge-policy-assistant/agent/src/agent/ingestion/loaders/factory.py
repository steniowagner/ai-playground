from typing import Literal

from agent.ingestion.loaders.local import LocalDocumentLoader


def create_document_loader(loader: Literal["local"]):
    match loader:
        case "local":
            return LocalDocumentLoader()
        case _:
            raise ValueError(f"Unsupported Document loader: {loader}")
