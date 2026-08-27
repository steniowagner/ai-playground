from incident_triage_assistant.domain.types import Tool

from .schema import QueryMetricsArgs

QUERY_METRICS_TOOL: Tool = {
    "name": "query_metrics",
    "description": "Retrieve bounded telemetry around the incident window.",
    "parameters": QueryMetricsArgs.model_json_schema(),
}
