import os
from typing import Any

from groq import APIError, Groq
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.exceptions import LLMToolGenerationError
from incident_triage_assistant.llm.prompts import (
    CORRECTIVE_MESSAGE_PROMPT,
    RETRY_TOOL_FAILED_PROMPT,
)
from incident_triage_assistant.llm.schema import (
    LLMResponse,
)
from incident_triage_assistant.tools.tools_registry import ToolRegistration
from incident_triage_assistant.tools.types import ToolCallResponse

from .exception_handler import handle_groq_exception
from .messages_handler import GroqMessageHandler
from .parsers import (
    parse_groq_response_to_llm_response,
    parse_tool_execution_response_to_groq_tool_call_response,
)


class GroqLLMClient(LLMClient):
    def __init__(self, tools_definitions: list[ToolRegistration]) -> None:
        self._tools = [
            {"type": "function", "function": tool.definition.model_dump()}
            for tool in tools_definitions
        ]
        self._message_handler = GroqMessageHandler()
        self._client = Groq()

    def _ask_to_groq(self) -> LLMResponse:
        max_tool_generation_attempts = int(os.getenv("GROQ_RETRY_COUNT"))
        retry_message = None

        for attempt in range(max_tool_generation_attempts):
            messages = self._message_handler.messages

            if retry_message is not None:
                messages = [*messages, retry_message]

            try:
                completion = self._client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL"),
                    tools=self._tools,
                    messages=messages,
                    reasoning_effort="none",
                    temperature=float(os.getenv("GROQ_TEMPERATURE")),
                )

                groq_message = completion.choices[0].message

                self._message_handler.add_assistant_message(groq_message)

                return parse_groq_response_to_llm_response(groq_message)

            except APIError as error:
                internal_error = handle_groq_exception(error)

                should_retry = (
                    isinstance(internal_error, LLMToolGenerationError)
                    and attempt < max_tool_generation_attempts - 1
                )

                if should_retry:
                    retry_message = {
                        "role": "user",
                        "content": RETRY_TOOL_FAILED_PROMPT,
                    }
                    continue

                raise internal_error from error

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

    def continue_after_invalid_result(
        self,
        validation_feedback: str,
    ) -> LLMResponse:
        self._message_handler.add_user_message(
            f"{CORRECTIVE_MESSAGE_PROMPT}\n\nValidation feedback:\n{validation_feedback}"
        )

        return self._ask_to_groq()

    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: Any
    ) -> ToolCallResponse:
        return parse_tool_execution_response_to_groq_tool_call_response(
            tool_call_id=tool_call_id, tool_name=tool_name, tool_response=tool_response
        )
