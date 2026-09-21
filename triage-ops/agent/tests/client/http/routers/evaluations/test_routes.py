from __future__ import annotations

import pytest
from httpx import AsyncClient
from triage_ops.evaluation.behavioral import BehavioralCaseResult
from triage_ops.evaluation.schema import EvaluationCase

from tests.client.http.support import (
    RecordingEvaluationCasesRepository,
    RecordingGraphRunner,
    RecordingRunEvaluationCaseService,
    RecordingSampleQuestionsRepository,
)

pytestmark = pytest.mark.unit


async def test_lists_development_cases_by_default(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    evaluation_case: EvaluationCase,
    evaluation_cases_repository: RecordingEvaluationCasesRepository,
) -> None:
    client, _, _ = http_client

    response = await client.get("/evaluations/")

    assert response.status_code == 200
    assert response.json() == [evaluation_case.model_dump(mode="json")]
    assert evaluation_cases_repository.find_all_calls == ["development"]


async def test_rejects_an_unknown_evaluation_split(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    evaluation_cases_repository: RecordingEvaluationCasesRepository,
) -> None:
    client, _, _ = http_client

    response = await client.get("/evaluations/?split=unknown")

    assert response.status_code == 422
    assert evaluation_cases_repository.find_all_calls == []


async def test_runs_one_evaluation_and_returns_its_final_score(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    evaluation_result: BehavioralCaseResult,
    run_evaluation_case_service: RecordingRunEvaluationCaseService,
) -> None:
    client, _, _ = http_client

    response = await client.post("/evaluations/dev-018/run")

    assert response.status_code == 200
    assert response.json() == evaluation_result.model_dump(mode="json")
    assert response.json()["score"]["passed"] is True
    assert run_evaluation_case_service.case_ids == ["dev-018"]


async def test_unknown_evaluation_case_returns_404(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    run_evaluation_case_service: RecordingRunEvaluationCaseService,
) -> None:
    client, _, _ = http_client
    run_evaluation_case_service.missing_case_ids.add("dev-999")

    response = await client.post("/evaluations/dev-999/run")

    assert response.status_code == 404
    assert response.json() == {"detail": "Evaluation case not found: dev-999"}
    assert run_evaluation_case_service.case_ids == ["dev-999"]


async def test_held_out_run_requires_explicit_confirmation(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    run_evaluation_case_service: RecordingRunEvaluationCaseService,
) -> None:
    client, _, _ = http_client

    response = await client.post("/evaluations/holdout-001/run")

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Held-out evaluation requires confirm_held_out=true and must not be "
            "used for prompt tuning."
        )
    }
    assert run_evaluation_case_service.case_ids == []


async def test_confirmed_held_out_run_reaches_the_service(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    run_evaluation_case_service: RecordingRunEvaluationCaseService,
) -> None:
    client, _, _ = http_client

    response = await client.post("/evaluations/holdout-001/run?confirm_held_out=true")

    assert response.status_code == 200
    assert run_evaluation_case_service.case_ids == ["holdout-001"]
