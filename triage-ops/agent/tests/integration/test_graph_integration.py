from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pytest
import triage_ops.graph.builder as builder_module
from langchain.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from triage_ops.domain.investigation.schema import (
    AdvisoryAction,
    InvestigationEvidence,
    InvestigationFailure,
    InvestigationResponse,
)
from triage_ops.graph import BuildGraphArgs, GraphRunner, build_graph
from triage_ops.graph.event_stream import (
    ApprovalRequiredEvent,
    BaseToolEvent,
    ExecutingProposalEvent,
    InvestigationCompletedEvent,
    ProposalExecutionFinishedEvent,
    ProposalRejectedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
)
from triage_ops.graph.nodes.check_scope import RequestScope, ScopeDecision
from triage_ops.graph.nodes.request_approvals import (
    ApprovalDecision,
    InvalidApprovalResponse,
)
from triage_ops.repositories import RepositoryDataError, RepositoryUnavailable
from triage_ops.repositories.deployments import JSONDeploymentsRepository
from triage_ops.repositories.feature_flags import JSONFeatureFlagsRepository
from triage_ops.repositories.incidents import (
    Incident,
    IncidentRepository,
    JSONIncidentRepository,
)
from triage_ops.repositories.logs import (
    FindLogsArgs,
    JSONLogsRepository,
    LogsRepository,
)
from triage_ops.repositories.maintenance_windows import (
    JSONMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import JSONMetricsRepository
from triage_ops.repositories.runbooks import JSONRunbooksRepository
from triage_ops.repositories.services import JSONServicesRepository
from triage_ops.services import (
    ServiceExecutionException,
    bootstrap_services,
)
from triage_ops.services.restart_service import RestartServiceArgs
from triage_ops.tools.bootstrap_tools import BootstrapToolsArgs, bootstrap_tools
from triage_ops.tools.get_incident import GetIncidentTool
from triage_ops.tools.query_logs import QueryLogsTool

from tests.support.factories import (
    make_ai_tool_message,
    make_incident,
    make_investigation_failure_response,
    make_investigation_response,
    make_restart_proposal,
    make_tool_call,
)
from tests.support.fakes import RecordingService, ScriptedGraphModel

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class SequentialIncidentRepository(IncidentRepository):
    def __init__(self, outcomes: Iterable[Incident | None | Exception]) -> None:
        self.outcomes = deque(outcomes)
        self.calls: list[str] = []

    def find_by_id(self, incident_id: str) -> Incident | None:
        self.calls.append(incident_id)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def find_all(self) -> list[Incident]:
        raise AssertionError("This test repository only supports find_by_id().")


class FailingLogsRepository(LogsRepository):
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls: list[FindLogsArgs] = []

    def find(self, args: FindLogsArgs):
        self.calls.append(args)
        raise self.error

    def find_all(self):
        raise AssertionError("This test repository only supports find().")


@dataclass
class Harness:
    model: ScriptedGraphModel
    graph: Any
    runner: GraphRunner

    async def start(self, message: str, thread_id: str = "thread-1") -> list[Any]:
        return [event async for event in self.runner.start(thread_id, message)]

    async def state(self, thread_id: str = "thread-1") -> dict[str, Any]:
        snapshot = await self.graph.aget_state(
            {"configurable": {"thread_id": thread_id}}
        )
        return snapshot.values


def harness(
    *,
    scopes: Iterable[RequestScope],
    agent_messages: Iterable[AIMessage],
    final_responses: Iterable[InvestigationResponse] = (),
    tools: list | None = None,
) -> Harness:
    model = ScriptedGraphModel(
        scopes=[ScopeDecision(scope=scope) for scope in scopes],
        agent_messages=agent_messages,
        final_responses=final_responses,
    )
    graph = build_graph(
        BuildGraphArgs(
            model=model,  # type: ignore[arg-type]
            checkpointer=InMemorySaver(),
            tools=tools or build_test_tools(),
        )
    )
    return Harness(model=model, graph=graph, runner=GraphRunner(graph))


def tool_call(name: str, args: dict[str, Any], id_: str) -> AIMessage:
    return make_ai_tool_message(make_tool_call(name, args, id_))


def completed_result(
    *, actions: list[Any] | None = None, **overrides: Any
) -> InvestigationResponse:
    return make_investigation_response(
        evidence=[
            InvestigationEvidence(
                source="get_incident",
                observation="The incident record was retrieved.",
            )
        ],
        recommended_actions=actions or [],
        **overrides,
    )


def completion_failure() -> InvestigationResponse:
    return make_investigation_failure_response()


def replace_tool(name: str, replacement: Any) -> list:
    return [
        replacement if tool.get_name() == name else tool for tool in build_test_tools()
    ]


def build_test_tools() -> list:
    return bootstrap_tools(
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


def replace_incident_tool(repository: IncidentRepository) -> list:
    return replace_tool("get_incident", GetIncidentTool(repository=repository))


def two_restart_proposals() -> list[Any]:
    return [
        make_restart_proposal(),
        make_restart_proposal(
            rationale="A second independently affected worker group must restart.",
            args=RestartServiceArgs(
                service="checkout-api",
                environment="production",
                strategy="immediate",
            ),
        ),
    ]


def investigation_messages(
    incident_id: str = "INC-1042", suffix: str = "1"
) -> list[AIMessage]:
    return [
        tool_call(
            "get_incident",
            {"incident_id": incident_id},
            f"incident-{suffix}",
        ),
        tool_call(
            "complete_investigation",
            {"incident_id": incident_id, "reason": "evidence_sufficient"},
            f"complete-{suffix}",
        ),
    ]


def install_restart_service(
    monkeypatch: pytest.MonkeyPatch,
    service: RecordingService,
) -> None:
    registry = bootstrap_services()
    registry["restart_service"] = service  # type: ignore[typeddict-item]
    monkeypatch.setattr(builder_module, "bootstrap_services", lambda: registry)


class TestBasicGraphPaths:
    async def test_out_of_scope_request_ends_without_agent_or_tools(self) -> None:
        app = harness(scopes=[RequestScope.OUT_OF_SCOPE], agent_messages=[])

        events = await app.start("Write a poem about the ocean")
        state = await app.state()

        assert app.model.agent.inputs == []
        assert not any(isinstance(event, BaseToolEvent) for event in events)
        assert state["messages"][-1].text.startswith("I can help with incident triage")

    async def test_greeting_finishes_without_tool_calls(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[AIMessage(content="Hello! I can help with operations.")],
        )

        events = await app.start("Hello")
        state = await app.state()

        assert not any(isinstance(event, BaseToolEvent) for event in events)
        assert state["messages"][-1].text == "Hello! I can help with operations."

    async def test_ordinary_lookup_calls_read_only_tool_and_answers(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call(
                    "get_service_context",
                    {"service": "checkout-api", "environment": "production"},
                    "service-1",
                ),
                AIMessage(content="The payments team owns checkout-api."),
            ],
        )

        events = await app.start("Who owns checkout-api in production?")
        state = await app.state()

        finished = [event for event in events if isinstance(event, ToolFinishedEvent)]
        assert len(finished) == 1
        assert finished[0].tool == "get_service_context"
        assert finished[0].ok is True
        assert state["messages"][-1].text == "The payments team owns checkout-api."
        assert state["final_result"] is None

    async def test_malformed_incident_id_produces_clarification_without_tools(
        self,
    ) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                AIMessage(content="Please provide the ID in exact INC-XXXX format.")
            ],
        )

        events = await app.start("Investigate INC1042")
        state = await app.state()

        assert not any(isinstance(event, BaseToolEvent) for event in events)
        assert state["is_incident_id_input_invalid"] is True
        assert state["authorized_incident_id"] is None

    async def test_unprefixed_id_requires_confirmation_then_authorizes_on_next_turn(
        self,
    ) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE, RequestScope.IN_SCOPE],
            agent_messages=[
                AIMessage(content="Please confirm INC-1042."),
                AIMessage(content="Confirmed. What would you like to inspect?"),
            ],
        )

        await app.start("Investigate incident 1042")
        first_state = await app.state()
        await app.start("yes")
        second_state = await app.state()

        assert first_state["pending_incident_id_confirmation"] == "INC-1042"
        assert first_state["authorized_incident_id"] is None
        assert second_state["pending_incident_id_confirmation"] is None
        assert second_state["authorized_incident_id"] == "INC-1042"
        assert second_state["is_incident_id_input_invalid"] is False

    async def test_unauthorized_incident_tool_call_is_blocked(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-9999"}, "incident-1"),
                AIMessage(content="I cannot use an incident ID you did not provide."),
            ],
        )

        events = await app.start("Investigate INC-1042")

        skipped = [event for event in events if isinstance(event, ToolSkippedEvent)]
        assert len(skipped) == 1
        assert skipped[0].tool == "get_incident"
        assert skipped[0].reason == "incident_id_not_authorized"


class TestInvestigationPaths:
    async def test_successful_investigation_produces_structured_result(self) -> None:
        expected = completed_result()
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "query_logs",
                    {
                        "service": "checkout-api",
                        "environment": "production",
                        "contains": "OrderMappingError",
                        "limit": 10,
                        "severity": ["ERROR"],
                        "start_time": "2026-07-10T14:00:00Z",
                        "end_time": "2026-07-10T15:00:00Z",
                    },
                    "logs-1",
                ),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[expected],
        )

        events = await app.start("Investigate INC-1042")
        completions = [
            event for event in events if isinstance(event, InvestigationCompletedEvent)
        ]

        assert [
            event.tool for event in events if isinstance(event, ToolFinishedEvent)
        ] == [
            "get_incident",
            "query_logs",
            "complete_investigation",
        ]
        assert len(completions) == 1
        assert completions[0].result == expected.outcome
        assert app.model.finalizer.inputs

    async def test_unknown_incident_produces_investigation_failure(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-9999"}, "incident-1"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-9999",
                        "reason": "incident_lookup_failed",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[completion_failure()],
        )

        events = await app.start("Investigate INC-9999")
        completed = next(
            event for event in events if isinstance(event, InvestigationCompletedEvent)
        )

        assert isinstance(completed.result, InvestigationFailure)
        assert completed.result.error_code == "NOT_FOUND"
        finished = [event for event in events if isinstance(event, ToolFinishedEvent)]
        assert finished[0].tool == "get_incident"
        assert finished[0].ok is False

    async def test_retryable_incident_failure_is_retried_once_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = SequentialIncidentRepository(
            [RepositoryUnavailable("temporary"), make_incident()]
        )
        tools = replace_incident_tool(repository)
        expected = completed_result()
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-2"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[expected],
            tools=tools,
        )

        events = await app.start("Investigate INC-1042")

        assert repository.calls == ["INC-1042", "INC-1042"]
        incident_events = [
            event
            for event in events
            if isinstance(event, ToolFinishedEvent) and event.tool == "get_incident"
        ]
        assert [event.ok for event in incident_events] == [False, True]

    async def test_retryable_incident_failure_exhausts_one_retry_then_finalizes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = SequentialIncidentRepository(
            [
                RepositoryUnavailable("temporary one"),
                RepositoryUnavailable("temporary two"),
            ]
        )
        tools = replace_incident_tool(repository)
        failure = InvestigationResponse(
            outcome=InvestigationFailure(
                incident_id="INC-1042",
                error_code="EXECUTION_ERROR",
                summary="The incident repository remained unavailable after retry.",
            )
        )
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-2"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "incident_lookup_failed",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[failure],
            tools=tools,
        )

        events = await app.start("Investigate INC-1042")

        assert repository.calls == ["INC-1042", "INC-1042"]
        incident_events = [
            event
            for event in events
            if isinstance(event, ToolFinishedEvent) and event.tool == "get_incident"
        ]
        assert [event.ok for event in incident_events] == [False, False]
        completed = next(
            event for event in events if isinstance(event, InvestigationCompletedEvent)
        )
        assert completed.result == failure.outcome

    async def test_supporting_evidence_failure_becomes_a_safe_limitation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = FailingLogsRepository(
            RepositoryDataError("secret log backend details")
        )
        query_logs = QueryLogsTool(repository=repository)
        tools = replace_tool("query_logs", query_logs)
        expected = completed_result(
            summary="The incident was investigated, but log evidence was unavailable.",
            confidence="low",
        )
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "query_logs",
                    {
                        "service": "checkout-api",
                        "environment": "production",
                        "contains": None,
                        "limit": 10,
                        "severity": ["ERROR"],
                        "start_time": "2026-07-10T14:00:00Z",
                        "end_time": "2026-07-10T15:00:00Z",
                    },
                    "logs-1",
                ),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[expected],
            tools=tools,
        )

        events = await app.start("Investigate INC-1042")

        assert len(repository.calls) == 1
        log_event = next(
            event
            for event in events
            if isinstance(event, ToolFinishedEvent) and event.tool == "query_logs"
        )
        assert log_event.ok is False
        completed = next(
            event for event in events if isinstance(event, InvestigationCompletedEvent)
        )
        assert completed.result == expected.outcome
        transcript = app.model.finalizer.inputs[0][1].text
        assert "Failed to query logs due to an internal error" in transcript
        assert "secret log backend details" not in transcript

    async def test_non_retryable_incident_failure_is_not_executed_twice(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = SequentialIncidentRepository([RepositoryDataError("invalid data")])
        tools = replace_incident_tool(repository)
        failure = InvestigationResponse(
            outcome=InvestigationFailure(
                incident_id="INC-1042",
                error_code="EXECUTION_ERROR",
                summary="The incident repository was unavailable.",
            )
        )
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "incident_lookup_failed",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[failure],
            tools=tools,
        )

        events = await app.start("Investigate INC-1042")

        assert repository.calls == ["INC-1042"]
        assert any(isinstance(event, InvestigationCompletedEvent) for event in events)


class TestMultiTurnStatePaths:
    async def test_second_ordinary_turn_receives_history_once_in_order(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE, RequestScope.IN_SCOPE],
            agent_messages=[
                AIMessage(content="The payments team owns checkout-api."),
                AIMessage(content="Its primary runbook is RB-CHECKOUT-ERRORS."),
            ],
        )

        await app.start("Who owns checkout-api?")
        await app.start("Which runbook should that team use?")

        second_input = app.model.agent.inputs[1]
        conversation = [
            message
            for message in second_input
            if isinstance(message, (HumanMessage, AIMessage))
        ]
        assert [message.text for message in conversation] == [
            "Who owns checkout-api?",
            "The payments team owns checkout-api.",
            "Which runbook should that team use?",
        ]

    async def test_new_investigation_replaces_stale_authorization_approvals_and_evidence(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = SequentialIncidentRepository(
            [
                make_incident(incident_id="INC-1042"),
                make_incident(incident_id="INC-2042"),
            ]
        )
        tools = replace_incident_tool(repository)
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE, RequestScope.IN_SCOPE],
            agent_messages=[
                *investigation_messages("INC-1042", "old"),
                *investigation_messages("INC-2042", "new"),
            ],
            final_responses=[
                completed_result(actions=[make_restart_proposal()]),
                completed_result(incident_id="INC-2042"),
            ],
            tools=tools,
        )

        first_events = await app.start("Investigate INC-1042")
        first_action = next(
            event.actions[0]
            for event in first_events
            if isinstance(event, ApprovalRequiredEvent)
        )
        _ = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [
                    ApprovalDecision(
                        proposal_id=first_action["proposal_id"],
                        approved=True,
                    )
                ],
            )
        ]

        second_events = await app.start("Investigate INC-2042")

        assert repository.calls == ["INC-1042", "INC-2042"]
        completed = next(
            event
            for event in second_events
            if isinstance(event, InvestigationCompletedEvent)
        )
        assert completed.result.incident_id == "INC-2042"
        second_transcript = app.model.finalizer.inputs[1][1].text
        assert "INC-2042" in second_transcript
        assert "INC-1042" not in second_transcript
        state = await app.state()
        assert state["authorized_incident_id"] is None
        assert state["pending_approvals"] == []
        assert state["approval_decisions"] == []
        assert state["final_result"].incident_id == "INC-2042"
        assert len(service.calls) == 1


class TestApprovalAndCheckpointPaths:
    async def test_executable_proposal_interrupts_then_executes_after_approval(
        self,
    ) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[completed_result(actions=[make_restart_proposal()])],
        )

        initial_events = await app.start("Investigate INC-1042")
        approval_event = next(
            event
            for event in initial_events
            if isinstance(event, ApprovalRequiredEvent)
        )
        proposal_id = approval_event.actions[0]["proposal_id"]

        resumed_events = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [ApprovalDecision(proposal_id=proposal_id, approved=True)],
            )
        ]

        finished = next(
            event
            for event in resumed_events
            if isinstance(event, ProposalExecutionFinishedEvent)
        )
        assert finished.kind == "restart_service"
        assert finished.result["ok"] is True
        state = await app.state()
        assert state["pending_approvals"][0].status == "executed"

    async def test_multiple_executable_proposals_create_one_approval_each(
        self,
    ) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=investigation_messages(),
            final_responses=[completed_result(actions=two_restart_proposals())],
        )

        events = await app.start("Investigate INC-1042")

        approval_event = next(
            event for event in events if isinstance(event, ApprovalRequiredEvent)
        )
        assert len(approval_event.actions) == 2
        assert len({action["proposal_id"] for action in approval_event.actions}) == 2
        assert [action["args"]["strategy"] for action in approval_event.actions] == [
            "rolling",
            "immediate",
        ]
        state = await app.state()
        assert [record.status for record in state["pending_approvals"]] == [
            "pending",
            "pending",
        ]

    async def test_mixed_decisions_execute_only_the_approved_proposal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=investigation_messages(),
            final_responses=[completed_result(actions=two_restart_proposals())],
        )
        initial = await app.start("Investigate INC-1042")
        actions = next(
            event.actions
            for event in initial
            if isinstance(event, ApprovalRequiredEvent)
        )

        resumed = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [
                    ApprovalDecision(
                        proposal_id=actions[0]["proposal_id"],
                        approved=True,
                    ),
                    ApprovalDecision(
                        proposal_id=actions[1]["proposal_id"],
                        approved=False,
                    ),
                ],
            )
        ]

        assert len(service.calls) == 1
        assert service.calls[0].strategy == "rolling"
        state = await app.state()
        assert [record.status for record in state["pending_approvals"]] == [
            "executed",
            "rejected",
        ]
        finished = {
            str(event.proposal_id): event
            for event in resumed
            if isinstance(event, ProposalExecutionFinishedEvent)
        }
        rejected = next(
            event for event in resumed if isinstance(event, ProposalRejectedEvent)
        )
        assert finished[actions[0]["proposal_id"]].result["ok"] is True
        assert str(rejected.proposal_id) == actions[1]["proposal_id"]
        assert rejected.result is None

    async def test_service_execution_failure_emits_a_safe_failed_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService(
            error=ServiceExecutionException("secret provider failure")
        )
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=investigation_messages(),
            final_responses=[completed_result(actions=[make_restart_proposal()])],
        )
        initial = await app.start("Investigate INC-1042")
        action = next(
            event.actions[0]
            for event in initial
            if isinstance(event, ApprovalRequiredEvent)
        )

        resumed = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [
                    ApprovalDecision(
                        proposal_id=action["proposal_id"],
                        approved=True,
                    )
                ],
            )
        ]

        finished = next(
            event
            for event in resumed
            if isinstance(event, ProposalExecutionFinishedEvent)
        )
        assert finished.result["ok"] is False
        assert finished.result["error"]["code"] == "EXECUTION_ERROR"
        assert "secret provider failure" not in str(finished.result)
        assert len(service.calls) == 1
        state = await app.state()
        assert state["pending_approvals"][0].status == "failed"

    async def test_multiple_approved_actions_execute_once_in_proposal_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=investigation_messages(),
            final_responses=[completed_result(actions=two_restart_proposals())],
        )
        initial = await app.start("Investigate INC-1042")
        actions = next(
            event.actions
            for event in initial
            if isinstance(event, ApprovalRequiredEvent)
        )

        resumed = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [
                    ApprovalDecision(
                        proposal_id=actions[1]["proposal_id"],
                        approved=True,
                    ),
                    ApprovalDecision(
                        proposal_id=actions[0]["proposal_id"],
                        approved=True,
                    ),
                ],
            )
        ]

        assert [call.strategy for call in service.calls] == ["rolling", "immediate"]
        executing = [
            str(event.proposal_id)
            for event in resumed
            if isinstance(event, ExecutingProposalEvent)
        ]
        finished = [
            str(event.proposal_id)
            for event in resumed
            if isinstance(event, ProposalExecutionFinishedEvent)
        ]
        expected_order = [action["proposal_id"] for action in actions]
        assert executing == expected_order
        assert finished == expected_order

    async def test_advisory_only_result_ends_without_approval(self) -> None:
        advisory = AdvisoryAction(
            kind="advisory",
            rationale="Requires human coordination.",
            action="Contact the payment provider.",
        )
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[completed_result(actions=[advisory])],
        )

        events = await app.start("Investigate INC-1042")

        assert any(isinstance(event, InvestigationCompletedEvent) for event in events)
        assert not any(isinstance(event, ApprovalRequiredEvent) for event in events)

    async def test_separate_thread_ids_do_not_share_authorization_state(self) -> None:
        app = harness(
            scopes=[RequestScope.IN_SCOPE, RequestScope.IN_SCOPE],
            agent_messages=[
                AIMessage(content="Recorded first incident."),
                AIMessage(content="No incident was supplied."),
            ],
        )

        await app.start("Inspect INC-1042", thread_id="thread-a")
        await app.start("Who owns checkout-api?", thread_id="thread-b")

        first = await app.state("thread-a")
        second = await app.state("thread-b")
        assert first["authorized_incident_id"] == "INC-1042"
        assert second.get("authorized_incident_id") is None

    async def test_rejected_proposal_is_never_executed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=[
                tool_call("get_incident", {"incident_id": "INC-1042"}, "incident-1"),
                tool_call(
                    "complete_investigation",
                    {
                        "incident_id": "INC-1042",
                        "reason": "evidence_sufficient",
                    },
                    "complete-1",
                ),
            ],
            final_responses=[completed_result(actions=[make_restart_proposal()])],
        )
        initial = await app.start("Investigate INC-1042")
        approval_event = next(
            event for event in initial if isinstance(event, ApprovalRequiredEvent)
        )

        events = [
            event
            async for event in app.runner.resume(
                "thread-1",
                [
                    ApprovalDecision(
                        proposal_id=approval_event.actions[0]["proposal_id"],
                        approved=False,
                    )
                ],
            )
        ]

        rejected = [
            event for event in events if isinstance(event, ProposalRejectedEvent)
        ]
        assert len(rejected) == 1
        assert rejected[0].result is None
        assert service.calls == []

    async def test_invalid_resume_fails_without_executing_the_proposal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE],
            agent_messages=investigation_messages(),
            final_responses=[completed_result(actions=[make_restart_proposal()])],
        )
        initial = await app.start("Investigate INC-1042")
        action = next(
            event.actions[0]
            for event in initial
            if isinstance(event, ApprovalRequiredEvent)
        )
        invalid_resume = Command(
            resume={
                "decisions": [
                    {
                        "proposal_id": action["proposal_id"],
                        "approved": "yes",
                    }
                ]
            }
        )

        with pytest.raises(InvalidApprovalResponse):
            _ = [
                event async for event in app.runner._stream("thread-1", invalid_resume)
            ]

        assert service.calls == []
        state = await app.state()
        assert state["pending_approvals"][0].status == "pending"

    async def test_interleaved_threads_keep_interrupts_and_resumes_isolated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = RecordingService()
        install_restart_service(monkeypatch, service)
        app = harness(
            scopes=[RequestScope.IN_SCOPE, RequestScope.IN_SCOPE],
            agent_messages=[
                *investigation_messages(suffix="a"),
                *investigation_messages(suffix="b"),
            ],
            final_responses=[
                completed_result(actions=[make_restart_proposal()]),
                completed_result(actions=[make_restart_proposal()]),
            ],
        )

        first_events = await app.start("Investigate INC-1042", thread_id="thread-a")
        second_events = await app.start("Investigate INC-1042", thread_id="thread-b")
        first_action = next(
            event.actions[0]
            for event in first_events
            if isinstance(event, ApprovalRequiredEvent)
        )
        second_action = next(
            event.actions[0]
            for event in second_events
            if isinstance(event, ApprovalRequiredEvent)
        )

        second_resume = [
            event
            async for event in app.runner.resume(
                "thread-b",
                [
                    ApprovalDecision(
                        proposal_id=second_action["proposal_id"],
                        approved=True,
                    )
                ],
            )
        ]

        assert len(service.calls) == 1
        assert (await app.state("thread-a"))["pending_approvals"][0].status == "pending"
        assert (await app.state("thread-b"))["pending_approvals"][
            0
        ].status == "executed"
        assert {event.thread_id for event in second_resume} == {"thread-b"}

        first_resume = [
            event
            async for event in app.runner.resume(
                "thread-a",
                [
                    ApprovalDecision(
                        proposal_id=first_action["proposal_id"],
                        approved=False,
                    )
                ],
            )
        ]

        assert len(service.calls) == 1
        assert (await app.state("thread-a"))["pending_approvals"][
            0
        ].status == "rejected"
        assert (await app.state("thread-b"))["pending_approvals"][
            0
        ].status == "executed"
        assert {event.thread_id for event in first_resume} == {"thread-a"}
