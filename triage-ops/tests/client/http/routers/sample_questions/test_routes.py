from __future__ import annotations

import pytest
from httpx import AsyncClient
from triage_ops.repositories.sample_questions import SampleQuestions

from tests.client.http.support import (
    RecordingGraphRunner,
    RecordingSampleQuestionsRepository,
)

pytestmark = pytest.mark.unit


async def test_sample_questions_route_uses_the_lifespan_repository(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    sample_questions: SampleQuestions,
) -> None:
    client, _, sample_repository = http_client

    response = await client.get("/sample-questions/")

    assert response.status_code == 200
    assert response.json() == sample_questions.model_dump(mode="json")
    assert sample_repository.calls == 1
