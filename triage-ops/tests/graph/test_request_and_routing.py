from __future__ import annotations

from typing import Any

import pytest
import triage_ops.graph.nodes.reject_out_of_scope.node as rejection_module
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END
from triage_ops.domain.investigation.schema import (
    AdvisoryAction,
    InvestigationFailure,
)
from triage_ops.graph.conditions.after_finalize_investigation import (
    after_finalize_investigation,
)
from triage_ops.graph.conditions.after_llm_call import after_llm_call
from triage_ops.graph.conditions.after_scope_check import after_scope_check
from triage_ops.graph.conditions.after_tool_call import after_tool_call
from triage_ops.graph.nodes import Nodes
from triage_ops.graph.nodes.check_scope import RequestScope, ScopeDecision
from triage_ops.graph.nodes.check_scope.node import check_scope_node
from triage_ops.graph.nodes.llm_call.node import llm_call_node
from triage_ops.graph.nodes.prepare_user_request.node import prepare_user_request_node
from triage_ops.graph.nodes.reject_out_of_scope.node import (
    OUT_OF_SCOPE_RESPONSE,
    reject_out_of_scope_node,
)
from triage_ops.graph.nodes.utils import get_latest_user_message
from triage_ops.graph.state import State

from tests.support.factories import make_investigation_result, make_restart_proposal
from tests.support.fakes import ScriptedModel

pytestmark = pytest.mark.unit


def state_with_message(message: str, **updates: Any) -> State:
    values: dict[str, Any] = {"messages": [HumanMessage(content=message)]}
    values.update(updates)
    return State(**values)


class TestLatestUserMessage:
    def test_returns_latest_human_message(self) -> None:
        state = State(
            messages=[
                HumanMessage(content="first"),
                AIMessage(content="answer"),
                HumanMessage(content="latest"),
            ]
        )

        assert get_latest_user_message(state).text == "latest"  # type: ignore[union-attr]

    def test_returns_none_without_a_human_message(self) -> None:
        assert (
            get_latest_user_message(State(messages=[AIMessage(content="hi")])) is None
        )


class TestPrepareUserRequest:
    @pytest.mark.parametrize(
        "message",
        [
            "Investigate INC-1042",
            "Please inspect (INC-1042).",
            "INC-1042",
        ],
    )
    def test_authorizes_one_exact_incident_id(self, message: str) -> None:
        result = prepare_user_request_node(state_with_message(message))

        assert result == {
            "authorized_incident_id": "INC-1042",
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": False,
        }

    def test_deduplicates_repeated_occurrences_of_the_same_id(self) -> None:
        result = prepare_user_request_node(
            state_with_message("Compare INC-1042 with the details for INC-1042")
        )

        assert result["authorized_incident_id"] == "INC-1042"
        assert result["is_incident_id_input_invalid"] is False

    def test_rejects_multiple_distinct_incident_ids(self) -> None:
        result = prepare_user_request_node(
            state_with_message("Compare INC-1042 and INC-2042")
        )

        assert result == {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": True,
        }

    @pytest.mark.parametrize(
        "message",
        ["INC1042", "INC_1042", "INC-42", "inc-1042", "incident # 42"],
    )
    def test_rejects_malformed_incident_references(self, message: str) -> None:
        result = prepare_user_request_node(state_with_message(message))

        assert result["authorized_incident_id"] is None
        assert result["is_incident_id_input_invalid"] is True

    @pytest.mark.parametrize("message", ["incident 1042", "incident id: 1042"])
    def test_unprefixed_four_digit_id_requires_confirmation(self, message: str) -> None:
        result = prepare_user_request_node(state_with_message(message))

        assert result == {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": "INC-1042",
            "is_incident_id_input_invalid": True,
        }

    @pytest.mark.parametrize(
        "confirmation", ["yes", "Y!", "confirm", "confirmed.", "that's correct"]
    )
    def test_affirmative_confirmation_authorizes_pending_id(
        self, confirmation: str
    ) -> None:
        result = prepare_user_request_node(
            state_with_message(
                confirmation, pending_incident_id_confirmation="INC-1042"
            )
        )

        assert result == {
            "authorized_incident_id": "INC-1042",
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": False,
        }

    @pytest.mark.parametrize("confirmation", ["no", "N.", "incorrect"])
    def test_negative_confirmation_clears_pending_id(self, confirmation: str) -> None:
        result = prepare_user_request_node(
            state_with_message(
                confirmation, pending_incident_id_confirmation="INC-1042"
            )
        )

        assert result == {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": True,
        }

    def test_confirmation_without_pending_candidate_does_not_change_state(self) -> None:
        assert prepare_user_request_node(state_with_message("yes")) == {}

    def test_new_exact_id_replaces_pending_candidate(self) -> None:
        result = prepare_user_request_node(
            state_with_message(
                "Use INC-2042", pending_incident_id_confirmation="INC-1042"
            )
        )

        assert result["authorized_incident_id"] == "INC-2042"
        assert result["pending_incident_id_confirmation"] is None

    def test_unrelated_message_leaves_authorization_state_unchanged(self) -> None:
        assert (
            prepare_user_request_node(
                state_with_message(
                    "Show the checkout service owner",
                    authorized_incident_id="INC-1042",
                    is_incident_id_input_invalid=False,
                )
            )
            == {}
        )

    def test_state_without_human_message_is_ignored(self) -> None:
        assert (
            prepare_user_request_node(State(messages=[AIMessage(content="hi")])) == {}
        )


class TestScopeAndLlmNodes:
    @pytest.mark.parametrize(
        "scope", [RequestScope.IN_SCOPE, RequestScope.OUT_OF_SCOPE]
    )
    def test_scope_node_uses_only_prompt_and_latest_user_message(
        self, scope: RequestScope
    ) -> None:
        model = ScriptedModel([ScopeDecision(scope=scope)])
        latest = HumanMessage(content="latest request")
        state = State(
            messages=[
                HumanMessage(content="old request"),
                AIMessage(content="old answer"),
                latest,
            ]
        )

        result = check_scope_node(state, model=model)

        assert result == {"request_scope": scope}
        assert len(model.inputs[0]) == 2
        assert isinstance(model.inputs[0][0], SystemMessage)
        assert model.inputs[0][1] is latest

    def test_scope_node_ignores_state_without_user_message(self) -> None:
        model = ScriptedModel([])

        assert check_scope_node(State(messages=[]), model=model) == {}
        assert model.inputs == []

    def test_llm_node_adds_system_prompt_and_returns_model_message(self) -> None:
        response = AIMessage(content="Operational answer")
        model = ScriptedModel([response])
        user_message = HumanMessage(content="Who owns checkout-api?")

        result = llm_call_node(State(messages=[user_message]), model=model)

        assert result == {"messages": [response]}
        assert isinstance(model.inputs[0][0], SystemMessage)

    def test_llm_node_adds_pending_confirmation_instruction(self) -> None:
        model = ScriptedModel([AIMessage(content="Please confirm INC-1042")])
        state = state_with_message(
            "incident 1042", pending_incident_id_confirmation="INC-1042"
        )

        llm_call_node(state, model=model)

        system_messages = [
            message for message in model.inputs[0] if isinstance(message, SystemMessage)
        ]
        assert len(system_messages) == 2
        assert "INC-1042" in system_messages[1].text
        assert "not authorized" in system_messages[1].text

    @pytest.mark.xfail(
        strict=True,
        reason="llm_call_node currently appends state.messages twice",
    )
    def test_llm_node_includes_conversation_history_exactly_once(self) -> None:
        model = ScriptedModel([AIMessage(content="answer")])
        history = [
            HumanMessage(content="question"),
            AIMessage(content="prior answer"),
            HumanMessage(content="follow-up"),
        ]

        llm_call_node(State(messages=history), model=model)

        assert model.inputs[0][1:] == history


class TestOutOfScopeNode:
    def test_emits_and_stores_fixed_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        events: list[dict] = []
        monkeypatch.setattr(
            rejection_module, "get_stream_writer", lambda: events.append
        )

        result = reject_out_of_scope_node(State(messages=[]))

        assert result["messages"][0].text == OUT_OF_SCOPE_RESPONSE
        assert events == [
            {
                "event": rejection_module.CustomStreamEvents.MESSAGE_CHUNK,
                "content": OUT_OF_SCOPE_RESPONSE,
            }
        ]


class TestRoutingConditions:
    @pytest.mark.parametrize(
        ("scope", "expected"),
        [
            (RequestScope.IN_SCOPE, Nodes.LLM_CALL),
            (RequestScope.OUT_OF_SCOPE, Nodes.REJECT_OUT_OF_SCOPE),
            (None, Nodes.REJECT_OUT_OF_SCOPE),
        ],
    )
    def test_after_scope_check(self, scope: RequestScope | None, expected: Any) -> None:
        assert after_scope_check(State(messages=[], request_scope=scope)) == expected

    def test_after_llm_call_routes_tool_calls(self) -> None:
        message = AIMessage(
            content="",
            tool_calls=[{"name": "query_logs", "args": {}, "id": "call-1"}],
        )

        assert after_llm_call(State(messages=[message])) == Nodes.TOOL

    @pytest.mark.parametrize(
        "message", [AIMessage(content="answer"), HumanMessage(content="question")]
    )
    def test_after_llm_call_ends_without_tool_calls(self, message: Any) -> None:
        assert after_llm_call(State(messages=[message])) == END

    def test_after_tool_call_routes_completion_to_finalizer(self) -> None:
        state = State(
            messages=[
                ToolMessage(
                    content="{}",
                    name="query_logs",
                    tool_call_id="call-1",
                ),
                ToolMessage(
                    content="{}",
                    name="complete_investigation",
                    tool_call_id="call-2",
                ),
            ]
        )

        assert after_tool_call(state) == Nodes.FINALIZER

    def test_after_tool_call_only_inspects_trailing_tool_results(self) -> None:
        state = State(
            messages=[
                ToolMessage(
                    content="{}",
                    name="complete_investigation",
                    tool_call_id="call-1",
                ),
                AIMessage(content="later response"),
            ]
        )

        assert after_tool_call(state) == Nodes.LLM_CALL

    def test_finalizer_routes_executable_actions_to_approvals(self) -> None:
        state = State(
            messages=[],
            final_result=make_investigation_result(
                recommended_actions=[make_restart_proposal()]
            ),
        )

        assert after_finalize_investigation(state) == Nodes.PREPARE_APPROVALS

    @pytest.mark.parametrize(
        "final_result",
        [
            None,
            InvestigationFailure(
                incident_id="INC-1042",
                error_code="NOT_FOUND",
                summary="Incident not found.",
            ),
            make_investigation_result(),
            make_investigation_result(
                recommended_actions=[
                    AdvisoryAction(
                        kind="advisory",
                        rationale="A human must coordinate this step.",
                        action="Contact the provider.",
                    )
                ]
            ),
        ],
    )
    def test_finalizer_ends_without_executable_actions(self, final_result: Any) -> None:
        assert (
            after_finalize_investigation(State(messages=[], final_result=final_result))
            == END
        )
