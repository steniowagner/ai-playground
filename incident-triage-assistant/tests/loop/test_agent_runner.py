import json
from collections.abc import Iterable

import pytest
from incident_triage_assistant.investigation.schema import InvestigationResult
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.schema import LLMResponse, LLMToolCall
from incident_triage_assistant.loop.agent_runner import (
    MAX_INVALID_RESULT_ATTEMPTS,
    MAX_TOOL_CALL_ITERATIONS,
    AgentRunner,
)
from incident_triage_assistant.loop.errors import (
    AgentIterationLimitError,
    EmptyLLMReturn,
    InvalidInvestigationResultError,
)
from incident_triage_assistant.tools.types import (
    ToolCallResponse,
    ToolErrorResponse,
    ToolErrorResponseDetail,
)


class FakeToolsRegistry:
    def execute_tool(self, tool_name: str, raw_args: str):
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="NOT_FOUND",
                message=f"No fixture for {tool_name} with {raw_args}",
            ),
        )


class FakeLLMClient(LLMClient):
    def __init__(self, responses: Iterable[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.questions: list[str] = []
        self.tool_results: list[list[ToolCallResponse]] = []
        self.validation_feedback: list[str] = []

    def ask(self, question: str) -> LLMResponse:
        self.questions.append(question)
        return next(self.responses)

    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        self.tool_results.append(results)
        return next(self.responses)

    def continue_after_invalid_result(self, validation_feedback: str) -> LLMResponse:
        self.validation_feedback.append(validation_feedback)
        return next(self.responses)

    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: object
    ) -> ToolCallResponse:
        return ToolCallResponse(
            tool_call_id=tool_call_id,
            name=tool_name,
            content=str(tool_response),
        )


def valid_result_json() -> str:
    return json.dumps(
        {
            "incident_id": "INC-1043",
            "summary": "Payment failures correlate with a recent deployment.",
            "severity": "SEV2",
            "evidence": [
                {
                    "source": "get_incident",
                    "observation": "The incident affects payment-adapter in production.",
                }
            ],
            "likely_causes": [],
            "recommended_actions": [],
            "confidence": "medium",
            "requires_human_approval": False,
        }
    )


def final_response(content: str | None = None) -> LLMResponse:
    return LLMResponse(
        role="assistant",
        content=content if content is not None else valid_result_json(),
        tool_calls=None,
    )


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


def test_iterate_returns_validated_investigation_result() -> None:
    client = FakeLLMClient([final_response()])

    answer = AgentRunner(client, FakeToolsRegistry())._iterate("Question")

    assert isinstance(answer, InvestigationResult)
    assert answer.incident_id == "INC-1043"
    assert client.questions == ["Question"]


def test_iterate_runs_tool_then_returns_investigation_result() -> None:
    client = FakeLLMClient([tool_response(), final_response()])

    answer = AgentRunner(client, FakeToolsRegistry())._iterate("Investigate INC-1043")

    assert answer.incident_id == "INC-1043"
    assert len(client.tool_results) == 1
    assert client.tool_results[0][0].tool_call_id == "call-1"


def test_iterate_corrects_invalid_result_then_returns_valid_result() -> None:
    client = FakeLLMClient([final_response("not JSON"), final_response()])

    answer = AgentRunner(client, FakeToolsRegistry())._iterate("Investigate INC-1043")

    assert answer.incident_id == "INC-1043"
    assert len(client.validation_feedback) == 1
    assert "Invalid JSON" in client.validation_feedback[0]


def test_iterate_raises_after_invalid_result_attempts_are_exhausted() -> None:
    client = FakeLLMClient([final_response("not JSON")] * MAX_INVALID_RESULT_ATTEMPTS)

    with pytest.raises(InvalidInvestigationResultError) as raised:
        AgentRunner(client, FakeToolsRegistry())._iterate("Investigate INC-1043")

    assert raised.value.__cause__ is not None
    assert len(client.validation_feedback) == MAX_INVALID_RESULT_ATTEMPTS - 1


def test_iterate_rejects_empty_response() -> None:
    client = FakeLLMClient(
        [LLMResponse(role="assistant", content=None, tool_calls=None)]
    )

    with pytest.raises(EmptyLLMReturn):
        AgentRunner(client, FakeToolsRegistry())._iterate("Question")


def test_iterate_stops_before_tool_round_beyond_limit() -> None:
    client = FakeLLMClient([tool_response()] * (MAX_TOOL_CALL_ITERATIONS + 1))

    with pytest.raises(AgentIterationLimitError):
        AgentRunner(client, FakeToolsRegistry())._iterate("Question")

    assert len(client.tool_results) == MAX_TOOL_CALL_ITERATIONS
