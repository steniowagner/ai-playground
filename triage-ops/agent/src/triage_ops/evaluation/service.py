from typing import Protocol

from triage_ops.repositories.evaluation_cases import EvaluationCasesRepository

from .behavioral import BehavioralCaseResult
from .exceptions import EvaluationCaseNotFoundError
from .schema import EvaluationCase


class EvaluationCaseRunner(Protocol):
    async def run_case(self, case: EvaluationCase) -> BehavioralCaseResult: ...


class RunEvaluationCaseService:
    def __init__(
        self,
        *,
        cases_repository: EvaluationCasesRepository,
        runner: EvaluationCaseRunner,
    ) -> None:
        self._cases_repository = cases_repository
        self._runner = runner

    async def execute(self, case_id: str) -> BehavioralCaseResult:
        case = self._cases_repository.find_by_id(case_id)
        if case is None:
            raise EvaluationCaseNotFoundError(case_id)

        return await self._runner.run_case(case)
