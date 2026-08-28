from incident_triage_assistant.domain.types import Tool

from .schema import QueryMetricsArgs

# "description": "Retrieve bounded telemetry around the incident window.",
# "description": "Query metrics for one exact service and environment. The interval between start_time and end_time must not exceed 60 minutes.",

QUERY_METRICS_TOOL: Tool = {
    "name": "query_metrics",
    "description": "Query metrics for one exact service and environment. The interval between start_time and end_time must not exceed 60 minutes.",
    "parameters": QueryMetricsArgs.model_json_schema(),
}
