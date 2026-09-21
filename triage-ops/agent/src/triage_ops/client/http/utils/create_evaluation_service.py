import os

from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.evaluation.behavioral import (
    BehavioralEvaluationRunner,
    ModelBehavioralJudge,
)
from triage_ops.evaluation.service import RunEvaluationCaseService
from triage_ops.graph import BuildGraphArgs, GraphRunner, build_graph
from triage_ops.model import create_model
from triage_ops.repositories.deployments import JSONDeploymentsRepository
from triage_ops.repositories.evaluation_cases import EvaluationCasesRepository
from triage_ops.repositories.feature_flags import JSONFeatureFlagsRepository
from triage_ops.repositories.incidents import JSONIncidentRepository
from triage_ops.repositories.logs import JSONLogsRepository
from triage_ops.repositories.maintenance_windows import (
    JSONMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import JSONMetricsRepository
from triage_ops.repositories.runbooks import JSONRunbooksRepository
from triage_ops.repositories.services import JSONServicesRepository
from triage_ops.tools.bootstrap_tools import BootstrapToolsArgs, bootstrap_tools


def create_evaluation_service(
    cases_repository: EvaluationCasesRepository,
) -> RunEvaluationCaseService:
    subject_model = create_model("anthropic")
    judge_model = create_model(
        "anthropic",
        model_name=os.getenv("ANTHROPIC_EVALUATOR_MODEL"),
    )
    tools = bootstrap_tools(
        BootstrapToolsArgs(
            deployments_repository=JSONDeploymentsRepository(),
            feature_flags_repository=JSONFeatureFlagsRepository(),
            incidents_repository=JSONIncidentRepository(),
            logs_repository=JSONLogsRepository(),
            maintenance_windows_repository=JSONMaintenanceWindowsRepository(),
            metrics_repository=JSONMetricsRepository(),
            runbooks_repository=JSONRunbooksRepository(),
            services_repository=JSONServicesRepository(),
        )
    )
    graph = build_graph(
        BuildGraphArgs(
            model=subject_model,
            checkpointer=InMemorySaver(),
            tools=tools,
        )
    )
    runner = BehavioralEvaluationRunner(
        graph_runner=GraphRunner(graph),
        graph=graph,
        judge=ModelBehavioralJudge(judge_model),
    )
    return RunEvaluationCaseService(
        cases_repository=cases_repository,
        runner=runner,
    )
