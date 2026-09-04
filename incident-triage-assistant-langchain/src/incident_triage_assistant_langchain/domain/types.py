from typing import Literal

Environment = Literal["production", "staging"]

IncidentSeverity = Literal["SEV1", "SEV2", "SEV3", "SEV4"]

ConfidenceLevel = Literal["low", "medium", "high"]


ApprovalAction = Literal[
    "rollback_deployment",
    "disable_feature_flag",
    "restart_service",
    "escalate_incident",
]

EvidenceSource = Literal[
    "get_incident",
    "get_service_context",
    "get_recent_deployments",
    "query_metrics",
    "query_logs",
    "get_runbook",
    "get_maintenance_windows",
    "get_feature_flags",
]
