from incident_triage_assistant.tools.get_incident.definition import GET_INCIDENT_TOOL


def test_definition_uses_expected_tool_name() -> None:
    assert GET_INCIDENT_TOOL.name == "get_incident"


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_INCIDENT_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["incident_id"]
    assert tool_args["properties"]["incident_id"]["pattern"] == "^INC-[0-9]{4}$"
