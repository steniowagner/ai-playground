from groq.types.chat import ChatCompletionMessage
from incident_triage_assistant.llm.groq.parsers import (
    parse_groq_response_to_llm_response,
    parse_tool_execution_response_to_groq_tool_call_response,
)
from incident_triage_assistant.llm.schema import ToolCallResponse


def test_parse_final_assistant_response() -> None:
    message = ChatCompletionMessage(role="assistant", content="Final answer")

    response = parse_groq_response_to_llm_response(message)

    assert response.content == "Final answer"
    assert response.tool_calls is None


def test_parse_assistant_tool_call() -> None:
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

    response = parse_groq_response_to_llm_response(message)

    assert response.tool_calls is not None
    assert response.tool_calls[0].id == "call-1"
    assert response.tool_calls[0].name == "get_incident"
    assert response.tool_calls[0].serialized_arguments == (
        '{"incident_id":"INC-1043"}'
    )


def test_parse_tool_execution_response_returns_model() -> None:
    response = parse_tool_execution_response_to_groq_tool_call_response(
        tool_call_id="call-1",
        tool_name="get_incident",
        tool_response={"ok": True},
    )

    assert isinstance(response, ToolCallResponse)
    assert response.tool_call_id == "call-1"
    assert response.name == "get_incident"
    assert response.content == '{"ok": true}'


def test_parse_tool_execution_response_preserves_string_content() -> None:
    response = parse_tool_execution_response_to_groq_tool_call_response(
        tool_call_id="call-1",
        tool_name="get_incident",
        tool_response='{"ok":true}',
    )

    assert response.content == '{"ok":true}'
