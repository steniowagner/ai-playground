from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document_id: str
    content: str
    index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)
