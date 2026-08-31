from groq.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from incident_triage_assistant.llm.prompts import DEFAULT_SYSTEM_PROMPT


class GroqMessageHandler:
    def __init__(self) -> None:
        self._messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}
        ]

    @property
    def messages(self) -> list[ChatCompletionMessageParam]:
        return self._messages

    def add_user_message(self, content: str) -> None:
        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": content,
        }

        self._messages.append(message)

    def add_assistant_message(
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

    def add_tool_message(
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
