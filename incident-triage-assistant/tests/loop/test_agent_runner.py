from collections.abc import Iterable

import pytest
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.schema import (
    LLMResponse,
    LLMToolCall,
)
from incident_triage_assistant.loop.agent_runner import (
    MAX_TOOL_CALL_ITERATIONS,
    AgentRunner,
)
from incident_triage_assistant.loop.errors import (
    AgentIterationLimitError,
    EmptyLLMReturn,
)
from incident_triage_assistant.tools.tools_registry import ToolsRegistry
from incident_triage_assistant.tools.types import ToolCallResponse


class FakeLLMClient(LLMClient):
    def __init__(self, responses: Iterable[LLMResponse]) -> None:
        self.tools_registry = ToolsRegistry()
        self.responses = iter(responses)
        self.questions: list[str] = []
        self.tool_results: list[list[ToolCallResponse]] = []

    def ask(self, question: str) -> LLMResponse:
        self.questions.append(question)
        return next(self.responses)

    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        self.tool_results.append(results)
        return next(self.responses)

    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: object
    ) -> ToolCallResponse:
        return ToolCallResponse(
            tool_call_id=tool_call_id,
            name=tool_name,
            content=str(tool_response),
        )


def final_response(content: str = "Final answer") -> LLMResponse:
    return LLMResponse(role="assistant", content=content, tool_calls=None)


def tool_response() -> LLMResponse:
    return LLMResponse(
        role="assistant",
        content=None,
        tool_calls=[
            LLMToolCall(
                id="call-1",
                name="get_incident",
                args_str='{"incident_id":"INC-1043"}',
            )
        ],
    )


def test_iterate_returns_immediate_final_content() -> None:
    client = FakeLLMClient([final_response()])
    answer = AgentRunner(client)._iterate("Question")

    assert answer == "Final answer"
    assert client.questions == ["Question"]


def test_iterate_runs_tool_then_returns_final_content() -> None:
    client = FakeLLMClient([tool_response(), final_response("Incident found")])
    answer = AgentRunner(client)._iterate("Investigate INC-1043")

    assert answer == "Incident found"
    assert len(client.tool_results) == 1
    assert client.tool_results[0][0].tool_call_id == "call-1"


def test_iterate_rejects_empty_response() -> None:
    client = FakeLLMClient(
        [LLMResponse(role="assistant", content=None, tool_calls=None)]
    )

    with pytest.raises(EmptyLLMReturn):
        AgentRunner(client)._iterate("Question")


def test_iterate_stops_before_tool_round_beyond_limit() -> None:
    client = FakeLLMClient([tool_response()] * (MAX_TOOL_CALL_ITERATIONS + 1))

    with pytest.raises(AgentIterationLimitError):
        AgentRunner(client)._iterate("Question")

    assert len(client.tool_results) == MAX_TOOL_CALL_ITERATIONS
