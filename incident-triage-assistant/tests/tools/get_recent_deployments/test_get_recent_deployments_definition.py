from incident_triage_assistant.tools.get_recent_deployments.definition import (
    GET_RECENT_DEPLOYMENTS_TOOL,
)
def test_definition_uses_expected_tool_name() -> None:
    assert GET_RECENT_DEPLOYMENTS_TOOL.name == "get_recent_deployments"


def test_definition_disallows_additional_args() -> None:
    tool_args = GET_RECENT_DEPLOYMENTS_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == [
        "service",
        "environment",
        "started_at",
        "completed_at",
    ]
