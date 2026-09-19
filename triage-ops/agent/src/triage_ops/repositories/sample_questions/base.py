from abc import ABC, abstractmethod

from .schema import SampleQuestions


class SampleQuestionsRepository(ABC):
    @abstractmethod
    def find_all(self) -> SampleQuestions:
        pass
