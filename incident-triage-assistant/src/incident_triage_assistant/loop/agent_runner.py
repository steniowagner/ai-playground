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

from .errors import AgentIterationLimitError, EmptyLLMReturn

MAX_TOOL_CALL_ITERATIONS = 50


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

    def _iterate(self, question: str) -> str:
        response = self._llm_client.ask(question)
        tool_call_iterations = 0

        while True:
            if response.tool_calls:
                if tool_call_iterations >= MAX_TOOL_CALL_ITERATIONS:
                    raise AgentIterationLimitError()

                response = self._handle_tool_calls(response)
                tool_call_iterations += 1
                continue

            if response.content:
                return response.content

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
                print(f"\n{answer}")
            except (
                AgentIterationLimitError,
                EmptyLLMReturn,
                LLMError,
            ) as error:
                print(f"Unable to complete the investigation: {error}")
