from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from triage_ops.evaluation.exceptions import EvaluationCaseNotFoundError
from triage_ops.evaluation.schema import EvaluationCase
from triage_ops.evaluation.service import RunEvaluationCaseService

pytestmark = pytest.mark.evaluation


def evaluation_case() -> EvaluationCase:
    return EvaluationCase(
        case_id="dev-018",
        incident_id="INC-1042",
        user_request=("Triage INC-1042 using only evidence available by 14:07 UTC."),
        fixture_clock="2026-07-10T14:07:00Z",
        expected={
            "expected_confidence": "low",
            "must_not_use_future_evidence": True,
            "must_escalate": True,
        },
        tags=["temporal-consistency", "insufficient-evidence"],
    )


@dataclass
class RecordingCasesRepository:
    case: EvaluationCase | None
    requested_ids: list[str] = field(default_factory=list)

    def find_by_id(self, case_id: str) -> EvaluationCase | None:
        self.requested_ids.append(case_id)
        return self.case


@dataclass
class RecordingRunner:
    result: Any
    cases: list[EvaluationCase] = field(default_factory=list)

    async def run_case(self, case: EvaluationCase) -> Any:
        self.cases.append(case)
        return self.result


async def test_executes_the_selected_case_and_returns_its_result() -> None:
    case = evaluation_case()
    expected_result = object()
    repository = RecordingCasesRepository(case)
    runner = RecordingRunner(expected_result)
    service = RunEvaluationCaseService(
        cases_repository=repository,  # type: ignore[arg-type]
        runner=runner,
    )

    result = await service.execute("dev-018")

    assert result is expected_result
    assert repository.requested_ids == ["dev-018"]
    assert runner.cases == [case]


async def test_rejects_an_unknown_case_without_running_the_graph() -> None:
    repository = RecordingCasesRepository(None)
    runner = RecordingRunner(object())
    service = RunEvaluationCaseService(
        cases_repository=repository,  # type: ignore[arg-type]
        runner=runner,
    )

    with pytest.raises(EvaluationCaseNotFoundError) as error:
        await service.execute("dev-999")

    assert error.value.case_id == "dev-999"
    assert str(error.value) == "Evaluation case not found: dev-999"
    assert repository.requested_ids == ["dev-999"]
    assert runner.cases == []
