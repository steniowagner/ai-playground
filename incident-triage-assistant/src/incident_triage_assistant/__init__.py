from dotenv import load_dotenv

from incident_triage_assistant.llm.factory import create_llm_client
from incident_triage_assistant.loop.agent_runner import AgentRunner
from incident_triage_assistant.repositories.deployments.json import (
    JSONDeploymentsRepository,
)
from incident_triage_assistant.repositories.feature_flags.json import (
    JSONFeatureFlagsRepository,
)
from incident_triage_assistant.repositories.incidents.json import JSONIncidentRepository
from incident_triage_assistant.repositories.logs.json import JSONLogsRepository
from incident_triage_assistant.repositories.maintenance_windows.json import (
    JSONMaintenanceWindowsRepository,
)
from incident_triage_assistant.repositories.metrics.json import JSONMetricsRepository
from incident_triage_assistant.repositories.runbooks.json import JSONRunbooksRepository
from incident_triage_assistant.repositories.services.json import JSONServicesRepository
from incident_triage_assistant.tools.tools_registry import ToolsRegistry


def main() -> None:
    load_dotenv()

    json_incidents_repository = JSONIncidentRepository()
    json_services_repository = JSONServicesRepository()
    json_feature_flags_repository = JSONFeatureFlagsRepository()
    json_maintenance_windows_repository = JSONMaintenanceWindowsRepository()
    json_deployments_repository = JSONDeploymentsRepository()
    json_runbooks_repository = JSONRunbooksRepository()
    json_logs_repository = JSONLogsRepository()
    json_metrics_repository = JSONMetricsRepository()

    tools_registry = ToolsRegistry(
        incident_repository=json_incidents_repository,
        service_repository=json_services_repository,
        feature_flags_repository=json_feature_flags_repository,
        maintenance_windows_repository=json_maintenance_windows_repository,
        deployments_repository=json_deployments_repository,
        runbooks_repository=json_runbooks_repository,
        logs_repository=json_logs_repository,
        metrics_repository=json_metrics_repository,
    )

    tools_definitions = tools_registry.get_definitions()
    llm_client = create_llm_client("groq", tools_definitions)

    agent_runner = AgentRunner(llm_client=llm_client, tools_registry=tools_registry)
    agent_runner.run()
