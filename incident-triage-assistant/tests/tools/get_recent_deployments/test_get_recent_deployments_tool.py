import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.deployments.json import JSONDeploymentsRepository
from incident_triage_assistant.tools.get_recent_deployments.schema import Deployment
from incident_triage_assistant.tools.get_recent_deployments.tool import GetRecentDeploymentsTool
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)

get_recent_deployments = GetRecentDeploymentsTool(JSONDeploymentsRepository())


def test_return_tool_error_response_for_extra_args() -> None:
    response = get_recent_deployments(
        {
            "service": "web-gateway",
            "environment": "production",
            "started_at": "2026-07-09T16:00:00Z",
            "completed_at": "2026-07-09T18:00:00Z",
            "extra_field": True,
        }
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_for_invalid_args() -> None:
    response = get_recent_deployments(
        {
            "service": "web-gateway",
            "environment": "unknown_env",
            "started_at": "2026-07-09T16:00:00Z",
            "completed_at": "2026-07-09T18:00:00Z",
        }
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_for_invalid_query_window_args() -> None:
    response = get_recent_deployments(
        {"service": "web-gateway", "environment": "production"}
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_invalid_started_at() -> None:
    response = get_recent_deployments(
        {
            "service": "web-gateway",
            "environment": "production",
            "started_at": "not-datetime",
            "completed_at": "2026-07-09T17:08:00Z",
        }
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_invalid_completed_at() -> None:
    response = get_recent_deployments(
        {
            "service": "web-gateway",
            "environment": "production",
            "completed_at": "not-datetime",
            "started_at": "2026-07-09T17:08:00Z",
        }
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_started_at_after_completed_at() -> None:
    response = get_recent_deployments(
        {
            "service": "web-gateway",
            "environment": "production",
            "completed_at": "2026-07-09T17:08:00Z",
            "started_at": "2026-07-09T17:09:00Z",
        }
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_success_response_finds_deployment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployments_file = tmp_path / "deployments.json"

    deployments_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    {
                        "deployment_id": "dep-test-001",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T10:00:00Z",
                        "completed_at": "2026-08-20T10:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE",
        deployments_file,
    )

    response = get_recent_deployments(
        {
            "service": "checkout-api",
            "environment": "production",
            "started_at": "2026-08-20T09:00:00Z",
            "completed_at": "2026-08-20T11:00:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.ok == True
    assert isinstance(response.data.deployments, list)
    assert response.data.deployments[0].deployment_id == "dep-test-001"

    for deployment in response.data.deployments:
        Deployment.model_validate(deployment)


def test_return_deployments_sorted_desc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    deployments_file = tmp_path / "deployments.json"

    deployments_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    {
                        "deployment_id": "dep-8801",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "2026.07.09.3",
                        "commit": "2f41a63",
                        "started_at": "2026-07-09T17:00:00Z",
                        "completed_at": "2026-07-09T17:08:00Z",
                        "status": "succeeded",
                        "summary": "Improve checkout request tracing",
                    },
                    {
                        "deployment_id": "dep-8822",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "2026.07.10.1",
                        "commit": "89d3c14",
                        "started_at": "2026-07-10T13:58:00Z",
                        "completed_at": "2026-07-10T14:05:00Z",
                        "status": "succeeded",
                        "summary": "Require billing country during order mapping",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE",
        deployments_file,
    )

    response = get_recent_deployments(
        {
            "service": "checkout-api",
            "environment": "production",
            "started_at": "2026-07-09T00:00:00Z",
            "completed_at": "2026-07-11T00:00:00Z",
        }
    )

    completed_at = datetime.now(timezone.utc)
    for deployment in response.data.deployments:
        assert deployment.completed_at <= completed_at
        completed_at = deployment.completed_at


def test_filters_correctly_query_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployments_file = tmp_path / "deployments.json"

    deployments_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    {
                        "deployment_id": "dep-test-001",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T10:00:00Z",
                        "completed_at": "2026-08-20T10:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    },
                    {
                        "deployment_id": "dep-test-002",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T13:00:00Z",
                        "completed_at": "2026-08-20T13:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    },
                    {
                        "deployment_id": "dep-test-003",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T17:00:00Z",
                        "completed_at": "2026-08-20T17:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE",
        deployments_file,
    )

    response = get_recent_deployments(
        {
            "service": "checkout-api",
            "environment": "production",
            "started_at": "2026-08-20T13:04:00Z",
            "completed_at": "2026-08-20T17:15:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.ok == True
    assert isinstance(response.data.deployments, list)
    assert response.data.deployments[0].deployment_id == "dep-test-003"
    assert response.data.deployments[1].deployment_id == "dep-test-002"


def test_return_success_response_deployment_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployments_file = tmp_path / "deployments.json"

    deployments_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    {
                        "deployment_id": "dep-test-001",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T10:00:00Z",
                        "completed_at": "2026-08-20T10:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE",
        deployments_file,
    )

    response = get_recent_deployments(
        {
            "service": "auth-api",
            "environment": "production",
            "started_at": "2026-08-20T09:00:00Z",
            "completed_at": "2026-08-20T11:00:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.ok == True
    assert isinstance(response.data.deployments, list)
    assert len(response.data.deployments) == 0


def test_return_success_response_filter_deployment_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployments_file = tmp_path / "deployments.json"

    deployments_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    {
                        "deployment_id": "dep-test-001",
                        "service": "checkout-api",
                        "environment": "production",
                        "version": "1.2.3",
                        "commit": "abc123",
                        "started_at": "2026-08-20T10:00:00Z",
                        "completed_at": "2026-08-20T10:05:00Z",
                        "status": "succeeded",
                        "summary": "Test deployment",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE",
        deployments_file,
    )

    response = get_recent_deployments(
        {
            "service": "checkout-api",
            "environment": "production",
            "started_at": "2026-08-21T13:04:00Z",
            "completed_at": "2026-08-22T17:15:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.ok == True
    assert isinstance(response.data.deployments, list)
    assert len(response.data.deployments) == 0
