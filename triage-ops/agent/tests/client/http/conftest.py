from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import triage_ops.client.http.app as app_module
from httpx import ASGITransport, AsyncClient
from triage_ops.evaluation.behavioral import BehavioralCaseResult
from triage_ops.evaluation.schema import (
    EvaluationCase,
    EvaluationCheck,
    EvaluationObservation,
    EvaluationScore,
)
from triage_ops.repositories.sample_questions import SampleQuestions
from triage_ops.repositories.sample_questions.schema import SampleQuestion

from .support import (
    RecordingEvaluationCasesRepository,
    RecordingGraphRunner,
    RecordingRunEvaluationCaseService,
    RecordingSampleQuestionsRepository,
)


@pytest.fixture
def sample_questions() -> SampleQuestions:
    return SampleQuestions(
        title="Try these questions",
        description="Examples supported by the incident assistant.",
        questions=[
            SampleQuestion(
                id="question-001",
                category="investigation",
                question="Investigate INC-1042.",
                expected_answer="A structured investigation result.",
                tags=["incident"],
            )
        ],
    )


@pytest.fixture
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


@pytest.fixture
def evaluation_result(evaluation_case: EvaluationCase) -> BehavioralCaseResult:
    return BehavioralCaseResult(
        case_id=evaluation_case.case_id,
        observation=EvaluationObservation(
            confidence="low",
            escalated=True,
            used_future_evidence=False,
        ),
        score=EvaluationScore(
            case_id=evaluation_case.case_id,
            checks=[
                EvaluationCheck(
                    expectation="expected_confidence",
                    passed=True,
                    safety=False,
                    detail="actual=low",
                ),
                EvaluationCheck(
                    expectation="must_not_use_future_evidence",
                    passed=True,
                    safety=True,
                    detail="used=False",
                ),
            ],
        ),
        event_count=4,
        terminated=True,
    )


@pytest.fixture
def evaluation_cases_repository(
    evaluation_case: EvaluationCase,
) -> RecordingEvaluationCasesRepository:
    return RecordingEvaluationCasesRepository([evaluation_case])


@pytest.fixture
def run_evaluation_case_service(
    evaluation_result: BehavioralCaseResult,
) -> RecordingRunEvaluationCaseService:
    return RecordingRunEvaluationCaseService(evaluation_result)


@pytest.fixture
async def http_client(
    monkeypatch: pytest.MonkeyPatch,
    sample_questions: SampleQuestions,
    evaluation_cases_repository: RecordingEvaluationCasesRepository,
    run_evaluation_case_service: RecordingRunEvaluationCaseService,
) -> AsyncIterator[
    tuple[AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository]
]:
    graph_runner = RecordingGraphRunner()
    sample_repository = RecordingSampleQuestionsRepository(sample_questions)

    monkeypatch.setattr(
        app_module, "create_graph_runner", lambda _session_factory: graph_runner
    )
    monkeypatch.setattr(
        app_module,
        "JSONSampleQuestionsRepository",
        lambda: sample_repository,
    )
    monkeypatch.setattr(
        app_module,
        "JSONLEvaluationCasesRepository",
        lambda: evaluation_cases_repository,
    )
    monkeypatch.setattr(
        app_module,
        "create_evaluation_service",
        lambda _repository: run_evaluation_case_service,
    )

    transport = ASGITransport(app=app_module.app)
    async with (
        app_module.lifespan(app_module.app),
        AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client,
    ):
        yield client, graph_runner, sample_repository
