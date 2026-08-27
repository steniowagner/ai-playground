from incident_triage_assistant.tools.query_metrics.definition import (
    QUERY_METRICS_TOOL,
)
from incident_triage_assistant.tools.run_tool import get_tool


def test_definition_uses_registered_tool_name() -> None:
    tool_name = QUERY_METRICS_TOOL["name"]

    assert tool_name == "query_metrics"
    assert callable(get_tool(tool_name))


def test_definition_disallows_additional_args() -> None:
    tool_args = QUERY_METRICS_TOOL["parameters"]

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == [
        "service",
        "environment",
        "metric_names",
        "start_time",
        "end_time",
    ]
