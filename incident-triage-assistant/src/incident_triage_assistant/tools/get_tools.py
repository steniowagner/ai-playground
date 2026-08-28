from incident_triage_assistant.domain.types import Tool

from .get_feature_flags.definition import GET_FEATURE_FLAGS_TOOL
from .get_incident.definition import GET_INCIDENT_TOOL
from .get_maintenance_windows.definition import GET_MAINTENANCE_WINDOW_TOOL
from .get_recent_deployments.definition import GET_RECENT_DEPLOYMENTS_TOOL
from .get_runbook.definition import GET_RUNBOOK_TOOL
from .get_service_context.definition import GET_SERVICE_CONTEXT_TOOL
from .query_logs.definition import QUERY_LOGS_TOOL
from .query_metrics.definition import QUERY_METRICS_TOOL

tools = [
    GET_FEATURE_FLAGS_TOOL,
    GET_SERVICE_CONTEXT_TOOL,
    GET_INCIDENT_TOOL,
    GET_RECENT_DEPLOYMENTS_TOOL,
    QUERY_METRICS_TOOL,
    QUERY_LOGS_TOOL,
    GET_RUNBOOK_TOOL,
    GET_MAINTENANCE_WINDOW_TOOL,
]


def get_tools() -> list[Tool]:
    return [Tool.model_validate(tool) for tool in tools]
