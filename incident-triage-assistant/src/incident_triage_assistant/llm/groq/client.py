from typing import Any

from groq import Groq
from groq.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from incident_triage_assistant.llm.base import LLMClient
from incident_triage_assistant.llm.schema import (
    LLMResponse,
    ToolCallResponse,
)

from .parsers import GroqParsers


class GroqLLMClient(LLMClient):
    def __init__(self) -> None:
        super().__init__()
        self._tools = [
            {"type": "function", "function": tool.model_dump()} for tool in self._tools
        ]
        self._messages: list[ChatCompletionMessageParam] = []
        self._parsers = GroqParsers()
        self._client = Groq()

    def _add_user_message(self, content: str) -> None:
        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": content,
        }

        self._messages.append(message)

    def _add_assistant_message(
        self,
        groq_message: ChatCompletionMessage,
    ) -> None:
        history_message: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": groq_message.content,
        }

        if groq_message.tool_calls:
            history_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in groq_message.tool_calls
            ]

        self._messages.append(history_message)

    def _add_tool_message(
        self,
        tool_call_id: str,
        content: str,
    ) -> None:
        message: ChatCompletionToolMessageParam = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }

        self._messages.append(message)

    def _ask_to_groq(self) -> LLMResponse:
        completion = self._client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            tools=self._tools,
            messages=self._messages,
            reasoning_effort="none",
            temperature=0.2,
        )

        groq_message = completion.choices[0].message

        self._add_assistant_message(groq_message)

        return self._parsers.parse_groq_response_to_llm_response(groq_message)

    def ask(self, question: str) -> LLMResponse:
        self._add_user_message(question)

        return self._ask_to_groq()

    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        for result in results:
            self._add_tool_message(
                tool_call_id=result.tool_call_id, content=result.content
            )

        return self._ask_to_groq()

    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: Any
    ) -> ToolCallResponse:
        return self._parsers.parse_tool_execution_response_to_groq_tool_call_response(
            tool_call_id=tool_call_id, tool_name=tool_name, tool_response=tool_response
        )
