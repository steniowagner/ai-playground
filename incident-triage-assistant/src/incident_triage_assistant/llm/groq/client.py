from typing import Any

from groq import APIError, Groq
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.schema import (
    LLMResponse,
)
from incident_triage_assistant.tools.types import ToolCallResponse

from .exception_handler import handle_groq_exception
from .messages_handler import GroqMessageHandler
from .parsers import (
    parse_groq_response_to_llm_response,
    parse_tool_execution_response_to_groq_tool_call_response,
)


class GroqLLMClient(LLMClient):
    def __init__(self) -> None:
        super().__init__()
        self._tools = [
            {"type": "function", "function": tool.definition.model_dump()}
            for tool in self.tools_registry.get_registrations()
        ]
        self._message_handler = GroqMessageHandler()
        self._client = Groq()

    def _ask_to_groq(self) -> LLMResponse:
        try:
            completion = self._client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                tools=self._tools,
                messages=self._message_handler.messages,
                reasoning_effort="none",
                temperature=0.2,
            )
        except APIError as e:
            raise handle_groq_exception(e) from e

        groq_message = completion.choices[0].message

        self._message_handler.add_assistant_message(groq_message)

        return parse_groq_response_to_llm_response(groq_message)

    def ask(self, question: str) -> LLMResponse:
        self._message_handler.add_user_message(question)

        return self._ask_to_groq()

    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        for result in results:
            self._message_handler.add_tool_message(
                tool_call_id=result.tool_call_id, content=result.content
            )

        return self._ask_to_groq()

    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: Any
    ) -> ToolCallResponse:
        return parse_tool_execution_response_to_groq_tool_call_response(
            tool_call_id=tool_call_id, tool_name=tool_name, tool_response=tool_response
        )
