from incident_triage_assistant.tools.query_logs.definition import (
    QUERY_LOGS_TOOL,
)
from incident_triage_assistant.tools.run_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = QUERY_LOGS_TOOL["name"]

    assert tool_name == "query_logs"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_args() -> None:
    tool_args = QUERY_LOGS_TOOL["parameters"]

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == [
        "service",
        "environment",
        "start_time",
        "end_time",
    ]
