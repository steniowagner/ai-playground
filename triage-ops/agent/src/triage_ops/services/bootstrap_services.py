from .disable_feature_flag.service import DisableFeatureFlagService
from .escalate_incident.service import EscalateIncidentService
from .restart_service.service import RestartService
from .rollback_deployment.service import RoolbackDeploymentService
from .schema import ServiceRegistry


def bootstrap_services() -> ServiceRegistry:
    return {
        "rollback_deployment": RoolbackDeploymentService(),
        "disable_feature_flag": DisableFeatureFlagService(),
        "restart_service": RestartService(),
        "escalate_incident": EscalateIncidentService(),
    }
