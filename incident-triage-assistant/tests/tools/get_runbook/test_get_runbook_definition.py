from incident_triage_assistant.tools.get_runbook.definition import (
    GET_RUNBOOK_TOOL,
)
def test_definition_uses_expected_tool_name() -> None:
    assert GET_RUNBOOK_TOOL.name == "get_runbook"


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_RUNBOOK_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["runbook_id"]
