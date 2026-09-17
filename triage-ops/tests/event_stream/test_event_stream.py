from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from langchain.messages import AIMessageChunk, HumanMessage
from langchain_core.messages import HumanMessageChunk
from triage_ops.domain.investigation import InvestigationFailure
from triage_ops.graph import GraphRunner
from triage_ops.graph.event_stream.parse_custom_event import parse_custom_event
from triage_ops.graph.event_stream.parse_graph_event import parse_graph_event
from triage_ops.graph.event_stream.parse_message_event import (
    parse_message_event,
    split_stream_chunk,
)
from triage_ops.graph.event_stream.parse_update_event import parse_update_event
from triage_ops.graph.event_stream.schema import (
    ApprovalRequiredEvent,
    CustomStreamEvents,
    Event,
    ExecutingProposalEvent,
    InvestigationCompletedEvent,
    MessageChunkEvent,
    ModelThinkingEvent,
    ParseGraphEventArgs,
    ProposalExecutionFinishedEvent,
    ToolFailedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
    ToolStartedEvent,
)
from triage_ops.graph.nodes import Nodes
from triage_ops.graph.nodes.request_approvals import ApprovalDecision
from triage_ops.services import ServiceErrorResponse, ServiceSuccessResponse

from tests.support.factories import make_investigation_result, make_pending_approval

pytestmark = pytest.mark.unit

EVENT_ID = UUID("00000000-0000-0000-0000-000000000100")
PROPOSAL_ID = UUID("00000000-0000-0000-0000-000000000001")
PROPOSAL_2 = UUID("00000000-0000-0000-0000-000000000002")
PROPOSAL_3 = UUID("00000000-0000-0000-0000-000000000003")
PROPOSAL_4 = UUID("00000000-0000-0000-0000-000000000004")


def base_event() -> Event:
    return Event(event_id=EVENT_ID, thread_id="thread-1")


def approval(status: str, result: Any = None, proposal_id: UUID = PROPOSAL_ID):
    return make_pending_approval(
        proposal_id=proposal_id,
        status=status,  # type: ignore[arg-type]
        execution_result=result,
    )


class ScriptedStreamGraph:
    def __init__(self, stream: list[tuple[str, Any]]) -> None:
        self.stream = stream
        self.calls: list[dict[str, Any]] = []

    async def astream(self, **kwargs: Any):
        self.calls.append(kwargs)
        for item in self.stream:
            yield item


class TestMessageChunkSplitting:
    def test_plain_string_is_answer_content(self) -> None:
        chunk = AIMessageChunk(content="Hello")

        assert split_stream_chunk(chunk) == ("", "Hello")

    def test_combines_thinking_and_reasoning_blocks(self) -> None:
        chunk = AIMessageChunk(
            content=[
                {"type": "thinking", "thinking": "First. "},
                {"type": "reasoning", "reasoning": "Second."},
            ]
        )

        assert split_stream_chunk(chunk) == ("First. Second.", "")

    def test_combines_text_blocks_and_ignores_unknown_blocks(self) -> None:
        chunk = AIMessageChunk(
            content=[
                {"type": "text", "text": "Part one. "},
                {"type": "image", "url": "ignored"},
                "ignored",
                {"type": "text", "text": "Part two."},
            ]
        )

        assert split_stream_chunk(chunk) == ("", "Part one. Part two.")

    def test_handles_missing_block_content_as_empty(self) -> None:
        chunk = AIMessageChunk(content=[{"type": "thinking"}, {"type": "text"}])

        assert split_stream_chunk(chunk) == ("", "")


class TestMessageEventParsing:
    def test_parses_answer_chunk(self) -> None:
        event = parse_message_event(
            (AIMessageChunk(content="answer"), {"langgraph_node": Nodes.LLM_CALL}),
            base_event(),
        )

        assert isinstance(event, MessageChunkEvent)
        assert event.content == "answer"
        assert event.event_id == EVENT_ID
        assert event.thread_id == "thread-1"

    @pytest.mark.parametrize("block_type", ["thinking", "reasoning"])
    def test_parses_model_thinking_chunk(self, block_type: str) -> None:
        key = "thinking" if block_type == "thinking" else "reasoning"
        event = parse_message_event(
            (
                AIMessageChunk(
                    content=[{"type": block_type, key: "internal reasoning"}]
                ),
                {"langgraph_node": Nodes.LLM_CALL},
            ),
            base_event(),
        )

        assert isinstance(event, ModelThinkingEvent)
        assert event.content == "internal reasoning"

    def test_thinking_takes_precedence_when_chunk_contains_both(self) -> None:
        event = parse_message_event(
            (
                AIMessageChunk(
                    content=[
                        {"type": "thinking", "thinking": "reason"},
                        {"type": "text", "text": "answer"},
                    ]
                ),
                {"langgraph_node": Nodes.LLM_CALL},
            ),
            base_event(),
        )

        assert isinstance(event, ModelThinkingEvent)
        assert event.content == "reason"

    @pytest.mark.parametrize("node", [Nodes.CHECK_SCOPE, Nodes.FINALIZER])
    def test_hides_internal_model_nodes(self, node: Nodes) -> None:
        event = parse_message_event(
            (AIMessageChunk(content="hidden"), {"langgraph_node": node}),
            base_event(),
        )

        assert event is None

    def test_ignores_non_ai_chunks(self) -> None:
        event = parse_message_event(
            (HumanMessageChunk(content="user"), {}), base_event()
        )

        assert event is None

    def test_ignores_empty_ai_chunk(self) -> None:
        assert (
            parse_message_event((AIMessageChunk(content=""), {}), base_event()) is None
        )

    @pytest.mark.parametrize(
        "payload",
        [
            None,
            (),
            (AIMessageChunk(content="answer"),),
            (AIMessageChunk(content="x"), None),
        ],
    )
    def test_ignores_malformed_message_payload(self, payload: Any) -> None:
        assert parse_message_event(payload, base_event()) is None


class TestCustomEventParsing:
    @pytest.mark.parametrize(
        ("payload", "event_type", "expected"),
        [
            (
                {"event": CustomStreamEvents.MESSAGE_CHUNK, "content": "message"},
                MessageChunkEvent,
                {"content": "message"},
            ),
            (
                {
                    "event": CustomStreamEvents.TOOL_STARTED,
                    "tool": "query_logs",
                    "args": {"service": "checkout-api"},
                },
                ToolStartedEvent,
                {"tool": "query_logs", "arguments": {"service": "checkout-api"}},
            ),
            (
                {
                    "event": CustomStreamEvents.TOOL_FINISHED,
                    "tool": "query_logs",
                    "args": {},
                    "ok": True,
                },
                ToolFinishedEvent,
                {"ok": True},
            ),
            (
                {
                    "event": CustomStreamEvents.TOOL_FAILED,
                    "tool": "query_logs",
                    "args": {},
                    "code": "INVALID_ARGUMENT",
                },
                ToolFailedEvent,
                {"error_code": "INVALID_ARGUMENT"},
            ),
            (
                {
                    "event": CustomStreamEvents.TOOL_SKIPPED,
                    "tool": "query_logs",
                    "args": {},
                    "code": "repeated_tool_call",
                },
                ToolSkippedEvent,
                {"reason": "repeated_tool_call"},
            ),
            (
                {
                    "event": CustomStreamEvents.EXECUTING_PROPOSAL,
                    "kind": "restart_service",
                    "args": {"strategy": "rolling"},
                    "incident_id": "INC-1042",
                    "proposal_id": str(PROPOSAL_ID),
                },
                ExecutingProposalEvent,
                {
                    "kind": "restart_service",
                    "arguments": {"strategy": "rolling"},
                    "incident_id": "INC-1042",
                    "proposal_id": PROPOSAL_ID,
                },
            ),
        ],
    )
    def test_maps_custom_events(
        self, payload: dict, event_type: type, expected: dict[str, Any]
    ) -> None:
        event = parse_custom_event(payload, base_event())

        assert isinstance(event, event_type)
        for field, value in expected.items():
            assert getattr(event, field) == value
        assert event.event_id == EVENT_ID
        assert event.thread_id == "thread-1"

    def test_ignores_unknown_custom_event(self) -> None:
        assert parse_custom_event({"event": "unknown"}, base_event()) is None

    @pytest.mark.parametrize(
        "payload",
        [
            None,
            [],
            {},
            {"event": CustomStreamEvents.MESSAGE_CHUNK},
            {"event": CustomStreamEvents.TOOL_STARTED, "tool": "query_logs"},
            {
                "event": CustomStreamEvents.TOOL_FINISHED,
                "tool": "query_logs",
                "args": {},
            },
            {
                "event": CustomStreamEvents.TOOL_SKIPPED,
                "tool": "query_logs",
                "args": {},
            },
        ],
    )
    def test_ignores_malformed_custom_event(self, payload: Any) -> None:
        assert parse_custom_event(payload, base_event()) is None


class TestUpdateEventParsing:
    def test_converts_interrupt_to_approval_required_event(self) -> None:
        actions = [{"proposal_id": str(PROPOSAL_ID), "kind": "restart_service"}]
        payload = {"__interrupt__": (SimpleNamespace(value={"actions": actions}),)}

        events = parse_update_event(payload, base_event())

        assert len(events) == 1
        assert isinstance(events[0], ApprovalRequiredEvent)
        assert events[0].actions == actions

    @pytest.mark.parametrize(
        "outcome",
        [
            make_investigation_result(),
            InvestigationFailure(
                incident_id="INC-1042",
                error_code="NOT_FOUND",
                summary="Incident not found.",
            ),
        ],
    )
    def test_converts_final_result_to_completion_event(self, outcome: Any) -> None:
        events = parse_update_event(
            {"finalizer": {"final_result": outcome}}, base_event()
        )

        assert len(events) == 1
        assert isinstance(events[0], InvestigationCompletedEvent)
        assert events[0].result == outcome

    def test_emits_executing_proposal_event(self) -> None:
        events = parse_update_event(
            {"execute": {"pending_approvals": [approval("executing")]}},
            base_event(),
        )

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, ExecutingProposalEvent)
        assert event.kind == "restart_service"
        assert event.incident_id == "INC-1042"
        assert event.proposal_id == PROPOSAL_ID
        assert event.arguments["strategy"] == "rolling"
        assert event.result is None

    def test_emits_successful_proposal_result(self) -> None:
        execution_result = ServiceSuccessResponse(ok=True, data={"restarted": True})
        events = parse_update_event(
            {
                "execute": {
                    "pending_approvals": [approval("executed", execution_result)]
                }
            },
            base_event(),
        )

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, ProposalExecutionFinishedEvent)
        assert event.result == {
            "ok": True,
            "data": {"restarted": True},
            "error": None,
        }

    def test_emits_rejected_proposal_without_execution_result(self) -> None:
        events = parse_update_event(
            {"approval": {"pending_approvals": [approval("rejected")]}},
            base_event(),
        )

        assert len(events) == 1
        assert isinstance(events[0], ProposalExecutionFinishedEvent)
        assert events[0].result is None

    def test_emits_failed_proposal_result(self) -> None:
        execution_result = ServiceErrorResponse.model_validate(
            {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": "safe failure",
                    "input": {},
                },
            }
        )
        events = parse_update_event(
            {"execute": {"pending_approvals": [approval("failed", execution_result)]}},
            base_event(),
        )

        assert len(events) == 1
        assert isinstance(events[0], ProposalExecutionFinishedEvent)
        assert events[0].result["ok"] is False

    def test_emits_mixed_proposal_lifecycle_events_in_state_order(self) -> None:
        success = ServiceSuccessResponse(ok=True, data={"restarted": True})
        failure = ServiceErrorResponse.model_validate(
            {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": "The action failed safely.",
                    "input": {},
                },
            }
        )

        events = parse_update_event(
            {
                "execute": {
                    "pending_approvals": [
                        approval("pending"),
                        approval("approved", proposal_id=PROPOSAL_2),
                        approval("executing", proposal_id=PROPOSAL_3),
                        approval("executed", success, proposal_id=PROPOSAL_4),
                        approval("failed", failure, proposal_id=PROPOSAL_2),
                        approval("rejected", proposal_id=PROPOSAL_ID),
                    ]
                }
            },
            base_event(),
        )

        assert [event.proposal_id for event in events] == [
            PROPOSAL_3,
            PROPOSAL_4,
            PROPOSAL_2,
            PROPOSAL_ID,
        ]
        assert isinstance(events[0], ExecutingProposalEvent)
        assert all(
            isinstance(event, ProposalExecutionFinishedEvent) for event in events[1:]
        )
        assert [event.result for event in events[1:]] == [
            success.model_dump(mode="json"),
            failure.model_dump(mode="json"),
            None,
        ]

    @pytest.mark.parametrize(
        "payload",
        [
            None,
            [],
            "invalid",
            {},
            {"node": None},
            {"node": "not a dictionary"},
            {"node": {}},
            {"node": {"pending_approvals": None}},
            {"node": {"pending_approvals": "invalid"}},
            {"node": {"pending_approvals": [{}]}},
            {"node": {"final_result": {"wrong": "shape"}}},
            {"__interrupt__": None},
            {"__interrupt__": (SimpleNamespace(value={}),)},
            {"__interrupt__": (SimpleNamespace(value={"actions": "invalid"}),)},
            {"__interrupt__": (SimpleNamespace(value={"actions": ["invalid"]}),)},
            {"node": {"pending_approvals": [approval("pending")]}},
        ],
    )
    def test_ignores_irrelevant_updates(self, payload: Any) -> None:
        assert parse_update_event(payload, base_event()) == []

    def test_multiple_events_share_source_update_metadata(self) -> None:
        events = parse_update_event(
            {
                "finalizer": {"final_result": make_investigation_result()},
                "execute": {"pending_approvals": [approval("executing")]},
            },
            base_event(),
        )

        assert len(events) == 2
        assert {event.event_id for event in events} == {EVENT_ID}
        assert {event.thread_id for event in events} == {"thread-1"}


class TestGraphEventDispatcher:
    @pytest.mark.parametrize(
        ("mode", "payload", "event_type"),
        [
            (
                "messages",
                (AIMessageChunk(content="answer"), {}),
                MessageChunkEvent,
            ),
            (
                "custom",
                {"event": CustomStreamEvents.MESSAGE_CHUNK, "content": "custom"},
                MessageChunkEvent,
            ),
            (
                "updates",
                {"finalizer": {"final_result": make_investigation_result()}},
                InvestigationCompletedEvent,
            ),
        ],
    )
    def test_dispatches_each_supported_stream_mode(
        self, mode: str, payload: Any, event_type: type
    ) -> None:
        events = list(
            parse_graph_event(
                ParseGraphEventArgs(
                    mode=mode, payload=payload, thread_id="thread-dispatch"
                )
            )
        )

        assert len(events) == 1
        assert isinstance(events[0], event_type)
        assert isinstance(events[0].event_id, UUID)
        assert events[0].thread_id == "thread-dispatch"

    @pytest.mark.parametrize(
        ("mode", "payload"),
        [
            ("unknown", {}),
            ("messages", (HumanMessageChunk(content="user"), {})),
            ("custom", {"event": "unknown"}),
            ("updates", {}),
        ],
    )
    def test_returns_no_events_for_unsupported_or_irrelevant_payloads(
        self, mode: str, payload: Any
    ) -> None:
        assert (
            list(
                parse_graph_event(
                    ParseGraphEventArgs(
                        mode=mode, payload=payload, thread_id="thread-dispatch"
                    )
                )
            )
            == []
        )

    def test_assigns_a_unique_id_to_each_public_event_from_one_update(self) -> None:
        events = list(
            parse_graph_event(
                ParseGraphEventArgs(
                    mode="updates",
                    payload={
                        "finalizer": {
                            "final_result": make_investigation_result(),
                            "pending_approvals": [
                                approval("executing"),
                                approval("rejected", proposal_id=PROPOSAL_2),
                            ],
                        }
                    },
                    thread_id="thread-unique",
                )
            )
        )

        assert len(events) == 3
        assert len({event.event_id for event in events}) == 3
        assert {event.thread_id for event in events} == {"thread-unique"}


class TestGraphRunnerEventContract:
    @pytest.mark.asyncio
    async def test_preserves_cross_mode_order_identity_and_start_input(self) -> None:
        graph = ScriptedStreamGraph(
            [
                (
                    "messages",
                    (
                        AIMessageChunk(content="Investigating."),
                        {"langgraph_node": Nodes.LLM_CALL},
                    ),
                ),
                (
                    "custom",
                    {
                        "event": CustomStreamEvents.TOOL_STARTED,
                        "tool": "get_incident",
                        "args": {"incident_id": "INC-1042"},
                    },
                ),
                (
                    "updates",
                    {
                        "finalizer": {
                            "final_result": make_investigation_result(),
                            "pending_approvals": [
                                approval("executing"),
                                approval("rejected", proposal_id=PROPOSAL_2),
                            ],
                        }
                    },
                ),
            ]
        )
        runner = GraphRunner(graph)  # type: ignore[arg-type]

        events = [
            event
            async for event in runner.start("thread-runner", "Investigate INC-1042")
        ]

        assert [type(event) for event in events] == [
            MessageChunkEvent,
            ToolStartedEvent,
            InvestigationCompletedEvent,
            ExecutingProposalEvent,
            ProposalExecutionFinishedEvent,
        ]
        assert len({event.event_id for event in events}) == len(events)
        assert {event.thread_id for event in events} == {"thread-runner"}
        call = graph.calls[0]
        assert call["config"] == {"configurable": {"thread_id": "thread-runner"}}
        assert call["stream_mode"] == ["messages", "updates", "custom"]
        assert call["input"]["final_result"] is None
        assert isinstance(call["input"]["messages"][0], HumanMessage)
        assert call["input"]["messages"][0].text == "Investigate INC-1042"

    @pytest.mark.asyncio
    async def test_resume_serializes_decisions_for_the_same_thread(self) -> None:
        graph = ScriptedStreamGraph(
            [
                (
                    "custom",
                    {
                        "event": CustomStreamEvents.MESSAGE_CHUNK,
                        "content": "Approval recorded.",
                    },
                )
            ]
        )
        runner = GraphRunner(graph)  # type: ignore[arg-type]
        decision = ApprovalDecision(proposal_id=PROPOSAL_ID, approved=True)

        events = [
            event
            async for event in runner.resume(
                "thread-resume",
                [decision],
            )
        ]

        assert len(events) == 1
        assert isinstance(events[0], MessageChunkEvent)
        assert events[0].content == "Approval recorded."
        assert events[0].thread_id == "thread-resume"
        call = graph.calls[0]
        assert call["config"] == {"configurable": {"thread_id": "thread-resume"}}
        assert call["input"].resume == {"decisions": [decision.model_dump(mode="json")]}
