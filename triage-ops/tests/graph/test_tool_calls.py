from __future__ import annotations

from typing import Any

import pytest
import triage_ops.graph.nodes.tool_calls.node as tool_node_module
from langchain.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field
from triage_ops.graph.nodes.tool_calls.node import (
    is_authorized_incident_tool_call,
    tool_calls_node,
)
from triage_ops.graph.nodes.tool_calls.schema import ToolCallStreamEventCodes
from triage_ops.graph.nodes.tool_calls.utils import (
    find_matching_tool_results,
    find_messages_since_last_human_message,
    should_allow_tool_call,
)
from triage_ops.graph.state import State
from triage_ops.tools import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolSuccessResponse,
)

from tests.support.factories import (
    make_ai_tool_message as ai_call,
)
from tests.support.factories import (
    make_tool_call as call,
)
from tests.support.factories import (
    make_tool_result as tool_result,
)

pytestmark = pytest.mark.unit


class EchoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)


class EchoTool(BaseTool):
    name: str = "query_logs"
    description: str = "Test tool"
    args_schema: type[BaseModel] = EchoArgs
    calls: list[dict[str, Any]] = Field(default_factory=list)
    response: Any = None

    def _run(self, value: str) -> Any:
        self.calls.append({"value": value})
        return self.response or ToolSuccessResponse(ok=True, data={"echo": value})


class TestToolCallHistory:
    def test_finds_messages_only_since_latest_human_turn(self) -> None:
        latest = HumanMessage(content="latest")
        messages = [
            HumanMessage(content="old"),
            AIMessage(content="old answer"),
            latest,
            AIMessage(content="new answer"),
        ]

        assert find_messages_since_last_human_message(messages) == messages[2:]

    def test_returns_all_messages_when_no_human_message_exists(self) -> None:
        messages = [AIMessage(content="answer")]

        assert find_messages_since_last_human_message(messages) == messages

    def test_matches_name_and_exact_arguments_with_linked_result(self) -> None:
        target = call()
        different_args = call(args={"value": "two"}, id_="call-2")
        messages = [
            HumanMessage(content="question"),
            ai_call(target, different_args),
            tool_result(target, ok=True),
            tool_result(different_args, ok=True),
        ]

        assert find_matching_tool_results(messages, target) == [messages[2]]

    def test_ignores_identical_calls_from_a_previous_user_turn(self) -> None:
        target = call()
        messages = [
            HumanMessage(content="old"),
            ai_call(target),
            tool_result(target, ok=True),
            HumanMessage(content="new"),
        ]

        assert find_matching_tool_results(messages, target) == []

    def test_allows_first_call(self) -> None:
        assert should_allow_tool_call([HumanMessage(content="q")], call()) is True

    def test_blocks_repetition_after_success(self) -> None:
        target = call()
        messages = [ai_call(target), tool_result(target, ok=True)]

        assert should_allow_tool_call(messages, target) is False

    def test_blocks_repetition_after_non_retryable_failure(self) -> None:
        target = call()
        messages = [ai_call(target), tool_result(target, ok=False, retryable=False)]

        assert should_allow_tool_call(messages, target) is False

    def test_allows_one_retry_after_retryable_failure(self) -> None:
        target = call()
        messages = [ai_call(target), tool_result(target, ok=False, retryable=True)]

        assert should_allow_tool_call(messages, target) is True

    def test_blocks_second_retry(self) -> None:
        first = call(id_="call-1")
        second = call(id_="call-2")
        current = call(id_="call-3")
        messages = [
            ai_call(first),
            tool_result(first, ok=False, retryable=True),
            ai_call(second),
            tool_result(second, ok=False, retryable=True),
        ]

        assert should_allow_tool_call(messages, current) is False

    def test_retry_not_allowed_result_does_not_count_as_execution(self) -> None:
        target = call()
        messages = [
            ai_call(target),
            tool_result(
                target,
                ok=False,
                error_code="RETRY_NOT_ALLOWED",
            ),
        ]

        assert should_allow_tool_call(messages, target) is True


class TestIncidentAuthorization:
    @pytest.mark.parametrize("name", ["get_incident", "complete_investigation"])
    def test_allows_exact_authorized_incident(self, name: str) -> None:
        state = State(
            messages=[],
            is_incident_id_input_invalid=False,
            authorized_incident_id="INC-1042",
        )

        assert (
            is_authorized_incident_tool_call(
                state,
                call(name=name, args={"incident_id": "INC-1042"}),  # type: ignore[arg-type]
            )
            is True
        )

    @pytest.mark.parametrize(
        ("authorized_id", "requested_id", "invalid"),
        [
            ("INC-1042", "INC-2042", False),
            ("INC-1042", "inc-1042", False),
            ("INC-1042", None, False),
            ("INC-1042", "INC-1042", True),
            (None, "INC-1042", True),
        ],
    )
    def test_blocks_untrusted_incident_ids(
        self, authorized_id: str | None, requested_id: str | None, invalid: bool
    ) -> None:
        state = State(
            messages=[],
            is_incident_id_input_invalid=invalid,
            authorized_incident_id=authorized_id,
        )

        assert (
            is_authorized_incident_tool_call(
                state,
                call(name="get_incident", args={"incident_id": requested_id}),  # type: ignore[arg-type]
            )
            is False
        )

    def test_non_incident_tool_does_not_require_authorization(self) -> None:
        assert (
            is_authorized_incident_tool_call(
                State(messages=[]),
                call(name="query_logs"),  # type: ignore[arg-type]
            )
            is True
        )


class TestToolCallsNode:
    def run_node(
        self,
        monkeypatch: pytest.MonkeyPatch,
        state: State,
        tools: dict[str, BaseTool],
    ) -> tuple[dict, list[dict]]:
        events: list[dict] = []
        monkeypatch.setattr(
            tool_node_module, "get_stream_writer", lambda: events.append
        )
        return tool_calls_node(state, tools=tools), events

    @pytest.mark.parametrize(
        "last_message", [HumanMessage(content="q"), AIMessage(content="answer")]
    )
    def test_ignores_message_without_tool_calls(self, last_message: Any) -> None:
        assert tool_calls_node(State(messages=[last_message]), tools={}) == {
            "messages": []
        }

    def test_executes_known_tool_and_emits_lifecycle_events(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        requested_call = call()
        tool = EchoTool()
        result, events = self.run_node(
            monkeypatch,
            State(messages=[HumanMessage(content="q"), ai_call(requested_call)]),
            {tool.name: tool},
        )

        response = ToolSuccessResponse[Any].model_validate_json(
            result["messages"][0].content
        )
        assert response.data == {"echo": "one"}
        assert tool.calls == [{"value": "one"}]
        assert [event["event"] for event in events] == [
            tool_node_module.CustomStreamEvents.TOOL_STARTED,
            tool_node_module.CustomStreamEvents.TOOL_FINISHED,
        ]

    def test_preserves_multiple_tool_call_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first = call(args={"value": "one"}, id_="call-1")
        second = call(args={"value": "two"}, id_="call-2")
        tool = EchoTool()

        result, _ = self.run_node(
            monkeypatch,
            State(messages=[HumanMessage(content="q"), ai_call(first, second)]),
            {tool.name: tool},
        )

        assert [message.tool_call_id for message in result["messages"]] == [
            "call-1",
            "call-2",
        ]
        assert tool.calls == [{"value": "one"}, {"value": "two"}]

    def test_blocks_unauthorized_incident_call_before_tool_lookup(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        requested_call = call(name="get_incident", args={"incident_id": "INC-9999"})
        result, events = self.run_node(
            monkeypatch,
            State(
                messages=[ai_call(requested_call)],
                authorized_incident_id="INC-1042",
                is_incident_id_input_invalid=False,
            ),
            {},
        )

        response = ToolErrorResponse.model_validate_json(result["messages"][0].content)
        assert response.error.code == "INVALID_ARGUMENT"
        assert response.error.retryable is False
        assert events[0]["code"] == ToolCallStreamEventCodes.INCIDENT_ID_NOT_AUTHORIZED

    def test_returns_unknown_tool_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        requested_call = call(name="missing_tool")
        result, events = self.run_node(
            monkeypatch, State(messages=[ai_call(requested_call)]), {}
        )

        response = ToolErrorResponse.model_validate_json(result["messages"][0].content)
        assert response.error.code == "UNKNOWN_TOOL"
        assert events[-1]["code"] == ToolCallStreamEventCodes.UNKNOWN_TOOL

    def test_returns_invalid_argument_error_without_invoking_tool(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        requested_call = call(args={"value": ""})
        tool = EchoTool()
        result, events = self.run_node(
            monkeypatch,
            State(messages=[ai_call(requested_call)]),
            {tool.name: tool},
        )

        response = ToolErrorResponse.model_validate_json(result["messages"][0].content)
        assert response.error.code == "INVALID_ARGUMENT"
        assert tool.calls == []
        assert events[-1]["code"] == ToolCallStreamEventCodes.INVALID_ARGUMENTS

    def test_skips_repeated_successful_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        previous = call(id_="call-1")
        repeated = call(id_="call-2")
        tool = EchoTool()
        state = State(
            messages=[
                HumanMessage(content="q"),
                ai_call(previous),
                tool_result(previous, ok=True),
                ai_call(repeated),
            ]
        )

        result, events = self.run_node(monkeypatch, state, {tool.name: tool})

        response = ToolErrorResponse.model_validate_json(result["messages"][0].content)
        assert response.error.code == "RETRY_NOT_ALLOWED"
        assert tool.calls == []
        assert events[-1]["code"] == ToolCallStreamEventCodes.REPEATED_TOOL_CALL

    def test_emits_failed_result_code_from_tool_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tool = EchoTool(
            response=ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="EXECUTION_ERROR",
                    message="safe failure",
                    retryable=True,
                    input={"value": "one"},
                ),
            )
        )
        result, events = self.run_node(
            monkeypatch,
            State(messages=[ai_call(call())]),
            {tool.name: tool},
        )

        response = ToolErrorResponse.model_validate_json(result["messages"][0].content)
        assert response.error.code == "EXECUTION_ERROR"
        assert events[-1]["ok"] is False
        assert events[-1]["code"] == "EXECUTION_ERROR"
