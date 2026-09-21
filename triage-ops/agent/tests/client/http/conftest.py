from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import triage_ops.client.http.app as app_module
from httpx import ASGITransport, AsyncClient
from triage_ops.repositories.sample_questions import SampleQuestions
from triage_ops.repositories.sample_questions.schema import SampleQuestion

from .support import RecordingGraphRunner, RecordingSampleQuestionsRepository


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
async def http_client(
    monkeypatch: pytest.MonkeyPatch,
    sample_questions: SampleQuestions,
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

    transport = ASGITransport(app=app_module.app)
    async with (
        app_module.lifespan(app_module.app),
        AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client,
    ):
        yield client, graph_runner, sample_repository
