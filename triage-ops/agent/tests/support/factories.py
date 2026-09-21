from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from langchain.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from triage_ops.domain import (
    Deployment,
    Environment,
    FeatureFlag,
    Log,
    LogSeverity,
    MaintenanceWindow,
    Metric,
    MetricValues,
)
from triage_ops.domain import (
    Service as ServiceContext,
)
from triage_ops.domain.investigation.proposals import (
    DisableFeatureFlagProposal,
    EscalateIncidentProposal,
    RestartServiceProposal,
    RollbackDeploymentProposal,
)
from triage_ops.domain.investigation.schema import (
    AdvisoryAction,
    ExecutableProposal,
    InvestigationEvidence,
    InvestigationFailure,
    InvestigationResponse,
    InvestigationResult,
)
from triage_ops.graph.nodes.prepare_approvals import PendingApproval
from triage_ops.graph.nodes.prepare_approvals.schema import ApprovalStatus
from triage_ops.graph.nodes.request_approvals import ApprovalDecision
from triage_ops.repositories.incidents import Incident, IncidentAlert
from triage_ops.services import ServiceResponse
from triage_ops.services.disable_feature_flag import DisableFeatureFlagServiceArgs
from triage_ops.services.escalate_incident import EscalateIncidentServiceArgs
from triage_ops.services.restart_service import RestartServiceArgs
from triage_ops.services.rollback_deployment import RollbackDeploymentServiceArgs
from triage_ops.tools import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from triage_ops.tools.schema import ToolErrorResponseCode

DEFAULT_PROPOSAL_ID = UUID("00000000-0000-0000-0000-000000000001")


def at(hour: int = 14, minute: int = 0) -> datetime:
    return datetime(2026, 7, 10, hour, minute, tzinfo=UTC)


def make_human_message(content: str = "Investigate INC-1042") -> HumanMessage:
    return HumanMessage(content=content)


def make_ai_message(
    content: str = "",
    *,
    tool_calls: list[ToolCall] | None = None,
) -> AIMessage:
    return AIMessage(content=content, tool_calls=tool_calls or [])


def make_ai_message_chunk(content: Any = "answer") -> AIMessageChunk:
    return AIMessageChunk(content=content)


def make_tool_call(
    name: str = "query_logs",
    args: dict[str, Any] | None = None,
    id_: str = "call-1",
) -> ToolCall:
    return ToolCall(
        name=name,
        args={"value": "one"} if args is None else args,
        id=id_,
    )


def make_ai_tool_message(*tool_calls: ToolCall) -> AIMessage:
    return make_ai_message(tool_calls=list(tool_calls))


def make_tool_success(data: Any | None = None) -> ToolSuccessResponse[Any]:
    return ToolSuccessResponse[Any](
        ok=True,
        data={"result": "ok"} if data is None else data,
    )


def make_tool_error(
    *,
    code: ToolErrorResponseCode = "EXECUTION_ERROR",
    retryable: bool = False,
    input_: dict[str, Any] | None = None,
    message: str = "failed",
) -> ToolErrorResponse:
    return ToolErrorResponse(
        ok=False,
        error=ToolErrorResponseDetail(
            code=code,
            message=message,
            retryable=retryable,
            input=input_ or {},
        ),
    )


def make_tool_result(
    tool_call: ToolCall,
    *,
    ok: bool,
    retryable: bool = False,
    error_code: ToolErrorResponseCode = "EXECUTION_ERROR",
    data: Any | None = None,
) -> ToolMessage:
    response: ToolResponse[Any] = (
        make_tool_success(data)
        if ok
        else make_tool_error(
            code=error_code,
            retryable=retryable,
            input_=tool_call["args"],
        )
    )
    return ToolMessage(
        content=response.model_dump_json(),
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
    )


def make_incident(**overrides: Any) -> Incident:
    values: dict[str, Any] = {
        "incident_id": "INC-1042",
        "title": "Checkout error rate elevated",
        "environment": "production",
        "primary_service": "checkout-api",
        "alert_started_at": datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        "created_at": datetime(2026, 1, 15, 12, 5, tzinfo=UTC),
        "status": "investigating",
        "severity": "SEV2",
        "reported_symptoms": ["Elevated HTTP 5xx responses"],
        "alert": IncidentAlert(
            metric="http_5xx_rate",
            observed=8.4,
            threshold=2.0,
            unit="percent",
        ),
    }
    values.update(overrides)
    return Incident(**values)


def make_rollback_proposal(**overrides: Any) -> RollbackDeploymentProposal:
    values: dict[str, Any] = {
        "rationale": "The errors began immediately after the retrieved deployment.",
        "args": RollbackDeploymentServiceArgs(
            service="checkout-api",
            environment="production",
            deployment_id="dep-882",
            target_deployment_id="dep-880",
        ),
    }
    values.update(overrides)
    return RollbackDeploymentProposal(**values)


def make_disable_feature_flag_proposal(
    **overrides: Any,
) -> DisableFeatureFlagProposal:
    values: dict[str, Any] = {
        "rationale": "The retrieved flag change correlates with the incident.",
        "args": DisableFeatureFlagServiceArgs(
            service="checkout-api",
            environment="production",
            flag_key="checkout_require_billing_country",
        ),
    }
    values.update(overrides)
    return DisableFeatureFlagProposal(**values)


def make_restart_proposal(**overrides: Any) -> RestartServiceProposal:
    values: dict[str, Any] = {
        "rationale": "Workers are wedged according to the retrieved logs.",
        "args": RestartServiceArgs(
            service="checkout-api",
            environment="production",
            strategy="rolling",
        ),
    }
    values.update(overrides)
    return RestartServiceProposal(**values)


def make_escalate_proposal(**overrides: Any) -> EscalateIncidentProposal:
    values: dict[str, Any] = {
        "rationale": "The observed impact exceeds the recorded severity.",
        "args": EscalateIncidentServiceArgs(
            incident_id="INC-1042",
            to_severity="SEV1",
            notify_team="payments",
        ),
    }
    values.update(overrides)
    return EscalateIncidentProposal(**values)


def make_advisory_proposal(**overrides: Any) -> AdvisoryAction:
    values: dict[str, Any] = {
        "kind": "advisory",
        "rationale": "More evidence is needed before taking a mutating action.",
        "action": "Collect representative trace samples and contact the owning team.",
    }
    values.update(overrides)
    return AdvisoryAction(**values)


def make_investigation_result(**overrides: Any) -> InvestigationResult:
    values: dict[str, Any] = {
        "incident_id": "INC-1042",
        "summary": "Checkout errors correlate with wedged workers.",
        "severity": "SEV2",
        "evidence": [
            InvestigationEvidence(
                source="get_incident",
                observation="The incident reports elevated checkout errors.",
            )
        ],
        "likely_causes": [],
        "recommended_actions": [],
        "confidence": "medium",
    }
    values.update(overrides)
    return InvestigationResult(**values)


def make_investigation_failure(**overrides: Any) -> InvestigationFailure:
    values: dict[str, Any] = {
        "incident_id": "INC-9999",
        "error_code": "NOT_FOUND",
        "summary": "The incident record could not be retrieved.",
        "retryable": False,
    }
    values.update(overrides)
    return InvestigationFailure(**values)


def make_investigation_response(**overrides: Any) -> InvestigationResponse:
    return InvestigationResponse(outcome=make_investigation_result(**overrides))


def make_investigation_failure_response(**overrides: Any) -> InvestigationResponse:
    return InvestigationResponse(outcome=make_investigation_failure(**overrides))


def make_pending_approval(
    proposal_id: UUID = DEFAULT_PROPOSAL_ID,
    *,
    status: ApprovalStatus = "pending",
    proposal: ExecutableProposal | None = None,
    execution_result: ServiceResponse[Any] | None = None,
    incident_id: str = "INC-1042",
) -> PendingApproval:
    return PendingApproval(
        proposal_id=proposal_id,
        incident_id=incident_id,
        proposal=make_restart_proposal() if proposal is None else proposal,
        status=status,
        execution_result=execution_result,
    )


def make_approval_decision(
    proposal_id: UUID = DEFAULT_PROPOSAL_ID,
    *,
    approved: bool = True,
) -> ApprovalDecision:
    return ApprovalDecision(proposal_id=proposal_id, approved=approved)


def make_deployment(
    deployment_id: str = "dep-882",
    *,
    service: str = "checkout-api",
    environment: Environment = "production",
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> Deployment:
    return Deployment(
        deployment_id=deployment_id,
        service=service,
        environment=environment,
        version="2026.07.10.1",
        commit="abc1234",
        started_at=started_at or at(13, 55),
        completed_at=completed_at or at(14, 5),
        status="succeeded",
        summary="Deploy checkout changes",
    )


def make_feature_flag(
    flag: str = "checkout_require_billing_country",
    *,
    service: str = "checkout-api",
    environment: Environment = "production",
) -> FeatureFlag:
    return FeatureFlag(
        flag=flag,
        service=service,
        environment=environment,
        enabled=True,
        owner_team="payments",
        changed_at=at(14, 5),
        changed_by_deployment="dep-882",
    )


def make_log(
    log_id: str = "log-1",
    timestamp: datetime | None = None,
    *,
    service: str = "checkout-api",
    environment: Environment = "production",
    severity: LogSeverity = "ERROR",
    message: str = "OrderMappingError occurred",
) -> Log:
    return Log(
        log_id=log_id,
        timestamp=timestamp or at(14, 10),
        service=service,
        environment=environment,
        severity=severity,
        trace_id="trace-1",
        message=message,
        attributes={},
    )


def make_metric(
    metric_id: str = "metric-1",
    timestamp: datetime | None = None,
    *,
    service: str = "checkout-api",
    environment: Environment = "production",
    values: MetricValues | None = None,
) -> Metric:
    return Metric(
        metric_id=metric_id,
        timestamp=timestamp or at(14, 10),
        service=service,
        environment=environment,
        values=values or MetricValues(error_rate=8.4, p95_latency_ms=900),
    )


def make_maintenance_window(
    maintenance_id: str = "MW-100",
    *,
    services: list[str] | None = None,
    environment: Environment = "production",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    status: str = "scheduled",
) -> MaintenanceWindow:
    return MaintenanceWindow(
        maintenance_id=maintenance_id,
        title="Database maintenance",
        services=services or ["checkout-api"],
        environment=environment,
        start_time=start_time or at(14),
        end_time=end_time or at(15),
        expected_effects=["Elevated latency"],
        approved_by="ops",
        status=status,  # type: ignore[arg-type]
    )


def make_service_context(
    name: str = "checkout-api",
    *,
    environments: list[Environment] | None = None,
) -> ServiceContext:
    return ServiceContext(
        service=name,
        display_name="Checkout API",
        description="Checkout service",
        tier=1,
        owner_team="payments",
        on_call="payments-primary",
        environments=environments or ["production"],
        dependencies=["payment-adapter"],
        runbook_ids=["RB-CHECKOUT-ERRORS"],
        slo={"availability_percent": 99.95},
    )
