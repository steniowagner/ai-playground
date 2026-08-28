from groq.types.chat import ChatCompletionMessage
from incident_triage_assistant.llm.groq.messages_handler import GroqMessageHandler


def test_add_user_message() -> None:
    handler = GroqMessageHandler()
    handler.add_user_message("Investigate INC-1043")

    assert handler.messages == [
        {"role": "user", "content": "Investigate INC-1043"}
    ]


def test_add_assistant_tool_call_message() -> None:
    handler = GroqMessageHandler()
    message = ChatCompletionMessage.model_validate(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "get_incident",
                        "arguments": '{"incident_id":"INC-1043"}',
                    },
                }
            ],
        }
    )
    handler.add_assistant_message(message)

    stored = handler.messages[0]
    assert stored["role"] == "assistant"
    assert stored["content"] is None
    assert stored["tool_calls"][0]["id"] == "call-1"
    assert stored["tool_calls"][0]["function"]["name"] == "get_incident"


def test_add_tool_result_message_preserves_call_id() -> None:
    handler = GroqMessageHandler()
    handler.add_tool_message("call-1", '{"ok":true}')

    assert handler.messages == [
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": '{"ok":true}',
        }
    ]
