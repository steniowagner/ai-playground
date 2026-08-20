from abc import ABC, abstractmethod

from agent.domain.document import Document


class DocumentLoader(ABC):
    @abstractmethod
    def load(self, source: str) -> Document:
        pass
