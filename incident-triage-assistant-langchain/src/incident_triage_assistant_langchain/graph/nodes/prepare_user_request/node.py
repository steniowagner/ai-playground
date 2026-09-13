import re

from incident_triage_assistant_langchain.graph.state import State
from langchain.messages import HumanMessage

VALID_INCIDENT_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])INC-\d{4}(?![A-Za-z0-9_-])")

MALFORMED_INCIDENT_REFERENCE_PATTERN = re.compile(
    r"\b(?:INC[-_\s]?\d+|incident(?:\s+id)?[\s:#-]*\d+)\b",
    re.IGNORECASE,
)


def get_latest_user_message(state: State) -> HumanMessage | None:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return message

    return None


def prepare_user_request_node(state: State) -> dict:
    user_message = get_latest_user_message(state)
    if user_message is None:
        return {}

    valid_incident_ids = set(VALID_INCIDENT_ID_PATTERN.findall(user_message.text))

    if len(valid_incident_ids) == 1:
        return {
            "authorized_incident_ids": valid_incident_ids,
            "incident_id_input_invalid": False,
        }

    if len(valid_incident_ids) > 1 or MALFORMED_INCIDENT_REFERENCE_PATTERN.search(
        user_message.text
    ):
        return {
            "authorized_incident_ids": set(),
            "incident_id_input_invalid": True,
        }

    return {"incident_id_input_invalid": False}
