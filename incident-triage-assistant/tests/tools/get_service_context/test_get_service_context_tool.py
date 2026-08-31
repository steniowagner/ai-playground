from incident_triage_assistant.repositories.services.json import JSONServicesRepository
from incident_triage_assistant.tools.get_service_context.schema import Service
from incident_triage_assistant.tools.get_service_context.tool import GetServiceContextTool
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)

get_service_context = GetServiceContextTool(JSONServicesRepository())


def test_return_tool_error_response_for_extra_args() -> None:
    response = get_service_context(
        {"service": "web-gateway", "environment": "production", "extra_field": True}
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_for_invalid_args() -> None:
    response = get_service_context(
        {"service": "web-gateway", "environment": "unknown_env"}
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "INVALID_ARGUMENT"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_tool_error_response_not_found_service_context() -> None:
    response = get_service_context(
        {"service": "unknown-service", "environment": "production"}
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.ok == False
    assert response.error.code == "NOT_FOUND"
    assert type(response.error.message) == str
    assert bool(response.error.message.strip()) == True


def test_return_existing_service_context() -> None:
    response = get_service_context(
        {"service": "catalog-api", "environment": "production"}
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.ok == True
    assert response.error == None
    assert isinstance(response.data.service, Service)
