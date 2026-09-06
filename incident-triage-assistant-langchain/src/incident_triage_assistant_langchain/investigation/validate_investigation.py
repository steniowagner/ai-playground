from typing import Any

from langchain.messages import AIMessage
from pydantic import TypeAdapter, ValidationError

from .exceptions import InvalidInvestigationResponse
from .schema import InvestigationFailure, InvestigationResult

INVESTIGATION_RESPONSE_ADAPTER = TypeAdapter(InvestigationResult | InvestigationFailure)


def validate_investigation_result(
    result: dict[str, Any],
) -> InvestigationResult | InvestigationFailure:
    messages = result.get("messages")
    if not messages:
        raise InvalidInvestigationResponse("The investigation produced no messages.")

    last_message = messages[-1]

    if not isinstance(last_message, AIMessage):
        raise InvalidInvestigationResponse(
            "The final investigation message is not an AI response."
        )

    if last_message.tool_calls:
        raise InvalidInvestigationResponse(
            "The investigation ended with unresolved tool calls."
        )

    if not isinstance(last_message.content, str):
        raise InvalidInvestigationResponse("The final response is not textual JSON.")

    try:
        return INVESTIGATION_RESPONSE_ADAPTER.validate_json(last_message.content)
    except ValidationError as exc:
        raise InvalidInvestigationResponse(
            "The final response does not match the required schema."
        ) from exc
