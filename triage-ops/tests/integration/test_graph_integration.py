from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pytest
import triage_ops.graph.builder as builder_module
from langchain.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.domain.investigation.schema import (
    AdvisoryAction,
    InvestigationEvidence,
    InvestigationFailure,
    InvestigationResponse,
)
from triage_ops.graph import GraphRunner, build_graph
from triage_ops.graph.event_stream import (
    ApprovalRequiredEvent,
    BaseToolEvent,
    InvestigationCompletedEvent,
    ProposalExecutionFinishedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
)
from triage_ops.graph.nodes.check_scope import RequestScope, ScopeDecision
from triage_ops.graph.nodes.request_approvals import ApprovalDecision
from triage_ops.repositories import RepositoryDataError, RepositoryUnavailable
from triage_ops.repositories.incidents import IncidentRepository
from triage_ops.tools import bootstrap_tools
from triage_ops.tools.get_incident import GetIncidentTool, Incident

from tests.support.factories import (
    make_ai_tool_message,
    make_incident,
    make_investigation_failure_response,
    make_investigation_response,
    make_restart_proposal,
    make_tool_call,
)
from tests.support.fakes import ScriptedGraphModel

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
) -> Harness:
    model = ScriptedGraphModel(
        scopes=[ScopeDecision(scope=scope) for scope in scopes],
        agent_messages=agent_messages,
        final_responses=final_responses,
    )
    graph = build_graph(model, InMemorySaver())  # type: ignore[arg-type]
    return Harness(model=model, graph=graph, runner=GraphRunner(graph))


def tool_call(name: str, args: dict[str, Any], id_: str) -> AIMessage:
    return make_ai_tool_message(make_tool_call(name, args, id_))


def completed_result(*, actions: list[Any] | None = None) -> InvestigationResponse:
    return make_investigation_response(
        evidence=[
            InvestigationEvidence(
                source="get_incident",
                observation="The incident record was retrieved.",
            )
        ],
        recommended_actions=actions or [],
    )


def completion_failure() -> InvestigationResponse:
    return make_investigation_failure_response()


def replace_incident_tool(repository: IncidentRepository) -> list:
    return [
        GetIncidentTool(repository=repository)
        if tool.get_name() == "get_incident"
        else tool
        for tool in bootstrap_tools()
    ]


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
        monkeypatch.setattr(builder_module, "bootstrap_tools", lambda: tools)
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
        )

        events = await app.start("Investigate INC-1042")

        assert repository.calls == ["INC-1042", "INC-1042"]
        incident_events = [
            event
            for event in events
            if isinstance(event, ToolFinishedEvent) and event.tool == "get_incident"
        ]
        assert [event.ok for event in incident_events] == [False, True]

    async def test_non_retryable_incident_failure_is_not_executed_twice(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = SequentialIncidentRepository([RepositoryDataError("invalid data")])
        tools = replace_incident_tool(repository)
        monkeypatch.setattr(builder_module, "bootstrap_tools", lambda: tools)
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
        )

        events = await app.start("Investigate INC-1042")

        assert repository.calls == ["INC-1042"]
        assert any(isinstance(event, InvestigationCompletedEvent) for event in events)


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

    async def test_rejected_proposal_is_never_executed(self) -> None:
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

        finished = next(
            event
            for event in events
            if isinstance(event, ProposalExecutionFinishedEvent)
        )
        assert finished.result is None
