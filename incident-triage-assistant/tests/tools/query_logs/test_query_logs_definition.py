from incident_triage_assistant.tools.query_logs.definition import (
    QUERY_LOGS_TOOL,
)
def test_definition_uses_expected_tool_name() -> None:
    assert QUERY_LOGS_TOOL.name == "query_logs"


def test_definition_disallows_additional_args() -> None:
    tool_args = QUERY_LOGS_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == [
        "service",
        "environment",
        "start_time",
        "end_time",
    ]
