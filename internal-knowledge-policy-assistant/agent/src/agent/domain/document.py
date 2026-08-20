from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Document:
    id: str
    content: str
    source: str
    type: Literal[".pdf", ".md"]
    metadata: dict[str, Any] = field(default_factory=dict)
