from incident_triage_assistant.tools.get_recent_deployments.definition import (
    GET_RECENT_DEPLOYMENTS_TOOL,
)
from incident_triage_assistant.tools.run_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = GET_RECENT_DEPLOYMENTS_TOOL["name"]

    assert tool_name == "get_recent_deployments"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_RECENT_DEPLOYMENTS_TOOL["parameters"]

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["service", "environment"]
