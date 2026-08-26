from incident_triage_assistant.tools.get_service_context.definition import (
    GET_SERVICE_CONTEXT_TOOL,
)
from incident_triage_assistant.tools.run_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = GET_SERVICE_CONTEXT_TOOL["name"]

    assert tool_name == "get_service_context"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_SERVICE_CONTEXT_TOOL["args"]

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["service", "environment"]
