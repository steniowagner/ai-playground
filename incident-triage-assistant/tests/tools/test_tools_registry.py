from incident_triage_assistant.tools.get_incident.schema import Incident
from incident_triage_assistant.tools.tools_registry import ToolsRegistry
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolRegistration,
    ToolSuccessResponse,
)


EXPECTED_TOOL_NAMES = {
    "get_feature_flags",
    "get_incident",
    "get_maintenance_windows",
    "get_recent_deployments",
    "get_runbook",
    "get_service_context",
    "query_logs",
    "query_metrics",
}


def test_registry_exposes_every_definition_with_a_handler() -> None:
    registrations = ToolsRegistry().get_registrations()

    assert all(isinstance(item, ToolRegistration) for item in registrations)
    assert {item.definition.name for item in registrations} == EXPECTED_TOOL_NAMES
    assert all(callable(item.handler) for item in registrations)


def test_registry_has_unique_tool_names() -> None:
    names = [
        registration.definition.name
        for registration in ToolsRegistry().get_registrations()
    ]

    assert len(names) == len(set(names))


def test_registry_executes_registered_tool() -> None:
    response = ToolsRegistry().execute_tool(
        "get_incident",
        '{"incident_id":"INC-1043"}',
    )

    assert isinstance(response, ToolSuccessResponse)
    assert isinstance(response.data.incident, Incident)
    assert response.data.incident.incident_id == "INC-1043"


def test_registry_returns_unknown_tool_error() -> None:
    response = ToolsRegistry().execute_tool("delete_database", "{}")

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "UNKNOWN_TOOL"


def test_registry_returns_invalid_argument_for_malformed_json() -> None:
    response = ToolsRegistry().execute_tool(
        "get_incident",
        '{"incident_id":',
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"


def test_registry_preserves_handler_validation_error() -> None:
    response = ToolsRegistry().execute_tool(
        "get_incident",
        '{"incident_id":"bad"}',
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
