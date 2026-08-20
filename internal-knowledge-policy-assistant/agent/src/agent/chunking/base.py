from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    content: str
    index: int
    token_count: int
    start_char: int
    end_char: int


class Chunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        pass
