from incident_triage_assistant.investigation.schema import InvestigationResult
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.exceptions import (
    LLMError,
)
from incident_triage_assistant.llm.schema import (
    LLMResponse,
    LLMToolCall,
)
from incident_triage_assistant.tools.tools_registry import ToolsRegistry
from incident_triage_assistant.tools.types import ToolCallResponse
from pydantic import ValidationError

from .errors import (
    AgentIterationLimitError,
    EmptyLLMReturn,
    InvalidInvestigationResultError,
)

MAX_TOOL_CALL_ITERATIONS = 15
MAX_INVALID_RESULT_ATTEMPTS = 2


class AgentRunner:
    def __init__(self, llm_client: LLMClient, tools_registry: ToolsRegistry) -> None:
        self._tools_registry = tools_registry
        self._llm_client = llm_client

    def _run_tool(self, tool_call: LLMToolCall) -> ToolCallResponse:
        tool_call_result = self._tools_registry.execute_tool(
            tool_call.name, tool_call.args_str
        )

        return self._llm_client.parse_tool_call_response(
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            tool_response=tool_call_result.model_dump_json(),
        )

    def _handle_tool_calls(self, llm_response: LLMResponse) -> LLMResponse:
        tools_calls_responses = [
            self._run_tool(tool_call) for tool_call in llm_response.tool_calls
        ]

        return self._llm_client.continue_with_tool_results(tools_calls_responses)

    def _iterate(self, question: str) -> InvestigationResult:
        response = self._llm_client.ask(question)

        tool_call_iterations = 0
        invalid_result_attempts = 0

        while True:
            if response.tool_calls:
                if tool_call_iterations >= MAX_TOOL_CALL_ITERATIONS:
                    raise AgentIterationLimitError()

                response = self._handle_tool_calls(response)
                tool_call_iterations += 1
                continue

            if response.content:
                try:
                    return InvestigationResult.model_validate_json(response.content)
                except ValidationError as error:
                    invalid_result_attempts += 1
                    feedback = str(error)

                    if invalid_result_attempts >= MAX_INVALID_RESULT_ATTEMPTS:
                        raise InvalidInvestigationResultError() from error

                    if any(item["loc"] == ("evidence",) for item in error.errors()):
                        feedback += (
                            "\nNo evidence was provided. Do not return final JSON. "
                            "Continue the investigation by calling the appropriate tools."
                        )

                    response = self._llm_client.continue_after_invalid_result(
                        feedback,
                    )

                    continue

            raise EmptyLLMReturn()

    def run(self):
        while True:
            question = input("\nQuestion: ").strip()

            if question.lower() == "exit":
                break

            if not question:
                continue

            try:
                answer = self._iterate(question)
                print(f"\n{answer.model_dump_json(indent=2)}")
            except (
                InvalidInvestigationResultError,
                AgentIterationLimitError,
                EmptyLLMReturn,
                LLMError,
            ) as error:
                print(f"Unable to complete the investigation: {error}")
