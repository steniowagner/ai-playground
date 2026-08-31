import pytest
from incident_triage_assistant.repositories.deployments.json import JSONDeploymentsRepository
from incident_triage_assistant.repositories.feature_flags.json import JSONFeatureFlagsRepository
from incident_triage_assistant.repositories.incidents.json import JSONIncidentRepository
from incident_triage_assistant.repositories.logs.json import JSONLogsRepository
from incident_triage_assistant.repositories.maintenance_windows.json import JSONMaintenanceWindowsRepository
from incident_triage_assistant.repositories.metrics.json import JSONMetricsRepository
from incident_triage_assistant.repositories.runbooks.json import JSONRunbooksRepository
from incident_triage_assistant.repositories.services.json import JSONServicesRepository
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


@pytest.fixture
def registry() -> ToolsRegistry:
    return ToolsRegistry(
        incident_repository=JSONIncidentRepository(),
        service_repository=JSONServicesRepository(),
        feature_flags_repository=JSONFeatureFlagsRepository(),
        maintenance_windows_repository=JSONMaintenanceWindowsRepository(),
        deployments_repository=JSONDeploymentsRepository(),
        runbooks_repository=JSONRunbooksRepository(),
        logs_repository=JSONLogsRepository(),
        metrics_repository=JSONMetricsRepository(),
    )


def test_registry_exposes_every_definition_with_a_handler(registry: ToolsRegistry) -> None:
    registrations = registry.get_definitions()

    assert all(isinstance(item, ToolRegistration) for item in registrations)
    assert {item.definition.name for item in registrations} == EXPECTED_TOOL_NAMES
    assert all(callable(item.handler) for item in registrations)


def test_registry_has_unique_tool_names(registry: ToolsRegistry) -> None:
    names = [
        registration.definition.name
        for registration in registry.get_definitions()
    ]

    assert len(names) == len(set(names))


def test_registry_executes_registered_tool(registry: ToolsRegistry) -> None:
    response = registry.execute_tool(
        "get_incident",
        '{"incident_id":"INC-1043"}',
    )

    assert isinstance(response, ToolSuccessResponse)
    assert isinstance(response.data.incident, Incident)
    assert response.data.incident.incident_id == "INC-1043"


def test_registry_returns_unknown_tool_error(registry: ToolsRegistry) -> None:
    response = registry.execute_tool("delete_database", "{}")

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "UNKNOWN_TOOL"


def test_registry_returns_invalid_argument_for_malformed_json(registry: ToolsRegistry) -> None:
    response = registry.execute_tool(
        "get_incident",
        '{"incident_id":',
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"


def test_registry_preserves_handler_validation_error(registry: ToolsRegistry) -> None:
    response = registry.execute_tool(
        "get_incident",
        '{"incident_id":"bad"}',
    )

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
