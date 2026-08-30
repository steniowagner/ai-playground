from incident_triage_assistant.tools.query_metrics.definition import (
    QUERY_METRICS_TOOL,
)
def test_definition_uses_expected_tool_name() -> None:
    assert QUERY_METRICS_TOOL.name == "query_metrics"


def test_definition_disallows_additional_args() -> None:
    tool_args = QUERY_METRICS_TOOL.parameters

    assert tool_args["additionalProperties"] is False
    assert tool_args["required"] == [
        "service",
        "environment",
        "metric_names",
        "start_time",
        "end_time",
    ]
