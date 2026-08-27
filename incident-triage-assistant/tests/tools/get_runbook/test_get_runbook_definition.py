from incident_triage_assistant.tools.get_runbook.definition import (
    GET_RUNBOOK_TOOL,
)
from incident_triage_assistant.tools.run_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = GET_RUNBOOK_TOOL["name"]

    assert tool_name == "get_runbook"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_RUNBOOK_TOOL["parameters"]

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["runbook_id"]
