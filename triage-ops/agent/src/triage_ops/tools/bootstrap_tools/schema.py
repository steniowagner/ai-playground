from dataclasses import dataclass

from triage_ops.repositories.deployments import DeploymentsRepository
from triage_ops.repositories.feature_flags import FeatureFlagsRepository
from triage_ops.repositories.incidents import IncidentRepository
from triage_ops.repositories.logs import LogsRepository
from triage_ops.repositories.maintenance_windows import MaintenanceWindowsRepository
from triage_ops.repositories.metrics import MetricsRepository
from triage_ops.repositories.runbooks import RunbooksRepository
from triage_ops.repositories.services import ServicesRepository


@dataclass(frozen=True)
class BootstrapToolsArgs:
    deployments_repository: DeploymentsRepository
    feature_flags_repository: FeatureFlagsRepository
    incidents_repository: IncidentRepository
    logs_repository: LogsRepository
    maintenance_windows_repository: MaintenanceWindowsRepository
    metrics_repository: MetricsRepository
    runbooks_repository: RunbooksRepository
    services_repository: ServicesRepository
