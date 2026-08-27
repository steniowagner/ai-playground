from incident_triage_assistant.domain.types import Tool

from .schema import QueryLogsArgs

QUERY_LOGS_TOOL: Tool = {
    "name": "query_logs",
    "description": "Retrieve a small, sanitized set of logs relevant to one service and incident window.",
    "parameters": QueryLogsArgs.model_json_schema(),
}
