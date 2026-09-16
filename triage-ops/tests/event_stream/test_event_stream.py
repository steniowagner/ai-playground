from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from langchain.messages import AIMessageChunk
from langchain_core.messages import HumanMessageChunk
from triage_ops.domain.investigation import InvestigationFailure
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
from triage_ops.graph.nodes.prepare_approvals import PendingApproval
from triage_ops.services import ServiceErrorResponse, ServiceSuccessResponse

from tests.support.factories import make_investigation_result, make_restart_proposal

pytestmark = pytest.mark.unit

EVENT_ID = UUID("00000000-0000-0000-0000-000000000100")
PROPOSAL_ID = UUID("00000000-0000-0000-0000-000000000001")


def base_event() -> Event:
    return Event(event_id=EVENT_ID, thread_id="thread-1")


def approval(status: str, result: Any = None) -> PendingApproval:
    return PendingApproval(
        proposal_id=PROPOSAL_ID,
        incident_id="INC-1042",
        proposal=make_restart_proposal(),
        status=status,  # type: ignore[arg-type]
        execution_result=result,
    )


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

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"node": None},
            {"node": "not a dictionary"},
            {"node": {}},
            {"node": {"pending_approvals": None}},
            {"node": {"pending_approvals": [approval("pending")]}},
        ],
    )
    def test_ignores_irrelevant_updates(self, payload: dict) -> None:
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
