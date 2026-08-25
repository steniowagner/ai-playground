from groq.types.chat import ChatCompletionMessage
from incident_triage_assistant.llm.groq.client import GroqLLMClient


def client_without_provider() -> GroqLLMClient:
    client = object.__new__(GroqLLMClient)
    client._messages = []
    return client


def test_add_user_message() -> None:
    client = client_without_provider()
    client._add_user_message("Investigate INC-1043")

    assert client._messages == [{"role": "user", "content": "Investigate INC-1043"}]


def test_add_assistant_tool_call_message() -> None:
    client = client_without_provider()
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
    client._add_assistant_message(message)

    stored = client._messages[0]
    assert stored["role"] == "assistant"
    assert stored["content"] is None
    assert stored["tool_calls"][0]["id"] == "call-1"
    assert stored["tool_calls"][0]["function"]["name"] == "get_incident"


def test_add_tool_result_message_preserves_call_id() -> None:
    client = client_without_provider()
    client._add_tool_message("call-1", '{"ok":true}')

    assert client._messages == [
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": '{"ok":true}',
        }
    ]
