from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.db import SessionFactory
from triage_ops.graph import BuildGraphArgs, GraphRunner, build_graph
from triage_ops.model import create_model
from triage_ops.repositories.deployments import JSONDeploymentsRepository
from triage_ops.repositories.feature_flags import (
    JSONFeatureFlagsRepository,
)
from triage_ops.repositories.incidents import (
    JSONIncidentRepository,
)
from triage_ops.repositories.logs import PostgresLogsRepository
from triage_ops.repositories.maintenance_windows import (
    JSONMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import (
    JSONMetricsRepository,
)
from triage_ops.repositories.runbooks import (
    JSONRunbooksRepository,
)
from triage_ops.repositories.services import (
    JSONServicesRepository,
)
from triage_ops.tools.bootstrap_tools import BootstrapToolsArgs, bootstrap_tools


def get_tools(session_factory: SessionFactory):
    return bootstrap_tools(
        BootstrapToolsArgs(
            deployments_repository=JSONDeploymentsRepository(),
            feature_flags_repository=JSONFeatureFlagsRepository(),
            incidents_repository=JSONIncidentRepository(),
            logs_repository=PostgresLogsRepository(session_factory=session_factory),
            maintenance_windows_repository=JSONMaintenanceWindowsRepository(),
            metrics_repository=JSONMetricsRepository(),
            runbooks_repository=JSONRunbooksRepository(),
            services_repository=JSONServicesRepository(),
        )
    )


def create_graph_runner(session_factory: SessionFactory) -> GraphRunner:
    model = create_model("anthropic")
    checkpointer = InMemorySaver()
    tools = get_tools(session_factory)
    return GraphRunner(
        build_graph(BuildGraphArgs(model=model, checkpointer=checkpointer, tools=tools))
    )
