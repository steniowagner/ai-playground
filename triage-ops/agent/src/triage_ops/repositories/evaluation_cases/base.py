from abc import ABC, abstractmethod
from typing import Literal

from triage_ops.evaluation.schema import EvaluationCase

type EvaluationSplit = Literal["development", "held_out"]


class EvaluationCasesRepository(ABC):
    @abstractmethod
    def find_all(self, split: EvaluationSplit) -> list[EvaluationCase]:
        pass

    @abstractmethod
    def find_by_id(self, case_id: str) -> EvaluationCase | None:
        pass
