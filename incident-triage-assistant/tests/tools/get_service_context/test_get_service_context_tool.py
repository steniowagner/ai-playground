from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.services.base import ServicesRepository
from incident_triage_assistant.tools.get_service_context.schema import Service
from incident_triage_assistant.tools.get_service_context.tool import (
    GetServiceContextTool,
)
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def service() -> Service:
    return Service(
        service="catalog-api",
        display_name="Catalog",
        description="Catalog API",
        tier=1,
        owner_team="catalog",
        on_call="catalog-oncall",
        environments=["production"],
        dependencies=[],
        runbook_ids=[],
        slo={"availability": 99.9},
    )


def test_returns_service_from_repository() -> None:
    repository = Mock(spec=ServicesRepository)
    repository.find.return_value = service()
    response = GetServiceContextTool(repository)(
        {"service": "catalog-api", "environment": "production"}
    )
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.service == service()
    repository.find.assert_called_once_with("catalog-api", "production")


def test_returns_not_found_when_repository_has_no_service() -> None:
    repository = Mock(spec=ServicesRepository)
    repository.find.return_value = None
    response = GetServiceContextTool(repository)(
        {"service": "unknown", "environment": "production"}
    )
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "NOT_FOUND"


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"service": "catalog-api", "environment": "unknown"},
        {"service": "catalog-api", "environment": "production", "extra": True},
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=ServicesRepository)
    response = GetServiceContextTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
