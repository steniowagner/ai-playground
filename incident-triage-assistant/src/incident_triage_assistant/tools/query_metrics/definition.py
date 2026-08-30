from incident_triage_assistant.tools.types import Tool

from .schema import QueryMetricsArgs

QUERY_METRICS_TOOL = Tool(
    name="query_metrics",
    description="Query selected metrics for one exact service and environment within a maximum 60-minute window. Returns timestamped measurements and evidence IDs; use the observations to investigate behavior without asking the tool to determine the root cause.",
    parameters=QueryMetricsArgs.model_json_schema(),
)
