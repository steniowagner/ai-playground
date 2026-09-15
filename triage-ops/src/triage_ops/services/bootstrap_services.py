from typing import TypedDict

from .disable_feature_flag.service import DisableFeatureFlagService
from .escalate_incident.service import EscalateIncidentService
from .restart_service.service import RestartService
from .rollback_deployment.service import RoolbackDeploymentService
from .service import Service


class ServiceRegistry(TypedDict):
    rollback_deployment: Service
    disable_feature_flag: Service
    restart_service: Service
    escalate_incident: Service


def bootstrap_services() -> ServiceRegistry:
    return {
        "rollback_deployment": RoolbackDeploymentService(),
        "disable_feature_flag": DisableFeatureFlagService(),
        "restart_service": RestartService(),
        "escalate_incident": EscalateIncidentService(),
    }
