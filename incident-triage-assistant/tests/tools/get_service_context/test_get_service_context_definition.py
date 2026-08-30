from incident_triage_assistant.tools.get_service_context.definition import (
    GET_SERVICE_CONTEXT_TOOL,
)
def test_definition_uses_expected_tool_name() -> None:
    assert GET_SERVICE_CONTEXT_TOOL.name == "get_service_context"


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_SERVICE_CONTEXT_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == ["service", "environment"]
