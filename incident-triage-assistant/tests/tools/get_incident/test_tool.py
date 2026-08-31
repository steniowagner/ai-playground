from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.incidents.base import IncidentRepository
from incident_triage_assistant.tools.get_incident.schema import Incident
from incident_triage_assistant.tools.get_incident.tool import GetIncidentTool
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def incident() -> Incident:
    return Incident.model_validate(
        {
            "incident_id": "INC-1043",
            "title": "Payment failures",
            "environment": "production",
            "primary_service": "payment-adapter",
            "alert_started_at": "2026-07-10T14:10:00Z",
            "created_at": "2026-07-10T14:12:00Z",
            "status": "investigating",
            "reported_symptoms": ["payments failing"],
            "alert": {
                "metric": "error_rate",
                "observed": 18.4,
                "threshold": 5.0,
                "unit": "percent",
            },
        }
    )


def test_returns_incident_from_repository() -> None:
    repository = Mock(spec=IncidentRepository)
    repository.find_by_id.return_value = incident()

    response = GetIncidentTool(repository)({"incident_id": "INC-1043"})

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.incident.incident_id == "INC-1043"
    repository.find_by_id.assert_called_once_with("INC-1043")


def test_returns_not_found_when_repository_has_no_incident() -> None:
    repository = Mock(spec=IncidentRepository)
    repository.find_by_id.return_value = None

    response = GetIncidentTool(repository)({"incident_id": "INC-9999"})

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "NOT_FOUND"


@pytest.mark.parametrize(
    "args", [{}, {"incident_id": "bad"}, {"incident_id": "INC-1043", "extra": True}]
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=IncidentRepository)

    response = GetIncidentTool(repository)(args)

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find_by_id.assert_not_called()
