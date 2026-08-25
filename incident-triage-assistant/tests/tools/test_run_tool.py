from incident_triage_assistant.tools.get_incident.schema import Incident
from incident_triage_assistant.tools.run_tool import get_tool, run_tool
from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolResponseSuccess,
)


def test_get_tool_returns_registered_callable() -> None:
    assert callable(get_tool("get_incident"))


def test_get_tool_returns_none_for_unknown_tool() -> None:
    assert get_tool("delete_database") is None


def test_run_tool_executes_registered_tool() -> None:
    response = run_tool("get_incident", '{"incident_id":"INC-1043"}')

    assert isinstance(response, ToolResponseSuccess)
    assert isinstance(response.data["incident"], Incident)
    assert response.data["incident"].incident_id == "INC-1043"


def test_run_tool_returns_unknown_tool_error() -> None:
    response = run_tool("delete_database", "{}")

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "UNKNOWN_TOOL"


def test_run_tool_returns_invalid_argument_for_malformed_json() -> None:
    response = run_tool("get_incident", '{"incident_id":')

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"


def test_run_tool_returns_invalid_argument_for_wrong_schema() -> None:
    response = run_tool("get_incident", '{"incident_id":"bad"}')

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
