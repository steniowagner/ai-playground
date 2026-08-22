from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationAnswer:
    content: str
    sources: list[str]
