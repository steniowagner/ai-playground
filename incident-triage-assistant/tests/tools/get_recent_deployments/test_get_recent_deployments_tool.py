from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.deployments.base import (
    DeploymentsRepository,
)
from incident_triage_assistant.tools.get_recent_deployments.schema import Deployment
from incident_triage_assistant.tools.get_recent_deployments.tool import (
    GetRecentDeploymentsTool,
)
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def deployment() -> Deployment:
    return Deployment.model_validate(
        {
            "deployment_id": "dep-1",
            "service": "checkout-api",
            "environment": "production",
            "version": "1.2.3",
            "commit": "abc123",
            "started_at": "2026-08-20T10:00:00Z",
            "completed_at": "2026-08-20T10:05:00Z",
            "status": "succeeded",
            "summary": "Tracing update",
        }
    )


def valid_args() -> dict[str, object]:
    return {
        "service": "checkout-api",
        "environment": "production",
        "started_at": "2026-08-20T09:00:00Z",
        "completed_at": "2026-08-20T11:00:00Z",
    }


def test_returns_repository_results_and_forwards_query() -> None:
    repository = Mock(spec=DeploymentsRepository)
    repository.find.return_value = [deployment()]
    response = GetRecentDeploymentsTool(repository)(valid_args())
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.deployments == [deployment()]
    args = repository.find.call_args.args[0]
    assert (args.service, args.environment) == ("checkout-api", "production")


def test_returns_empty_success_for_no_matches() -> None:
    repository = Mock(spec=DeploymentsRepository)
    repository.find.return_value = []
    response = GetRecentDeploymentsTool(repository)(valid_args())
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.deployments == []


@pytest.mark.parametrize(
    "args",
    [
        {},
        {
            "service": "checkout-api",
            "environment": "unknown",
            "started_at": "2026-08-20T09:00:00Z",
            "completed_at": "2026-08-20T11:00:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "started_at": "2026-08-20T11:00:00Z",
            "completed_at": "2026-08-20T09:00:00Z",
        },
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=DeploymentsRepository)
    response = GetRecentDeploymentsTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
