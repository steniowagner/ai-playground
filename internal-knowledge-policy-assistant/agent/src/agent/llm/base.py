from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def ask(self, question: str) -> str:
        pass
