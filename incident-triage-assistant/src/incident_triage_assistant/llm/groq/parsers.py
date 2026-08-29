import json
from typing import Any

from groq.types.chat import ChatCompletionMessage
from incident_triage_assistant.llm.schema import (
    LLMResponse,
    LLMToolCall,
)
from incident_triage_assistant.tools.types import ToolCallResponse


def parse_groq_response_to_llm_response(
    chat_completion_message: ChatCompletionMessage,
) -> LLMResponse:
    tool_calls = None

    if chat_completion_message.tool_calls:
        tool_calls = [
            LLMToolCall(
                id=message_tool_call.id,
                name=message_tool_call.function.name,
                args_str=message_tool_call.function.arguments,
            )
            for message_tool_call in chat_completion_message.tool_calls
        ]

    return LLMResponse(
        role=chat_completion_message.role,
        content=chat_completion_message.content,
        tool_calls=tool_calls,
    )


def parse_tool_execution_response_to_groq_tool_call_response(
    tool_call_id: str, tool_name: str, tool_response: Any
) -> ToolCallResponse:
    content = (
        json.dumps(tool_response)
        if not isinstance(tool_response, str)
        else tool_response
    )

    return ToolCallResponse(
        tool_call_id=tool_call_id,
        name=tool_name,
        content=content,
    )
