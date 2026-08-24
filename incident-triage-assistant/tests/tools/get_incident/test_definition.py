from incident_triage_assistant.tools.get_incident.definition import GET_INCIDENT_TOOL
from incident_triage_assistant.tools.get_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = GET_INCIDENT_TOOL["name"]

    assert tool_name == "get_incident"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_parameters() -> None:
    parameters = GET_INCIDENT_TOOL["parameters"]

    assert parameters["additionalProperties"] is False
    assert parameters["required"] == ["incident_id"]
    assert parameters["properties"]["incident_id"]["pattern"] == "^INC-[0-9]{4}$"
