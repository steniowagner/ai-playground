from typing import Literal

from .implementations.hugging_face import HuggingFaceFixedSizeChunker


def create_chunker(provider: Literal["hugging-face"]):
    match provider:
        case "hugging-face":
            return HuggingFaceFixedSizeChunker()
