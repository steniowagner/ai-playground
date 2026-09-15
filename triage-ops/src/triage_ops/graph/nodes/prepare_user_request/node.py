import re

from langchain.messages import HumanMessage
from triage_ops.graph.state import State

VALID_INCIDENT_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])INC-\d{4}(?![A-Za-z0-9_-])")

MALFORMED_INCIDENT_REFERENCE_PATTERN = re.compile(
    r"\b(?:INC[-_\s]?\d+|incident(?:\s+id)?[\s:#-]*\d+)\b",
    re.IGNORECASE,
)

UNPREFIXED_INCIDENT_ID_PATTERN = re.compile(
    r"\bincident(?:\s+id)?[\s:#-]*(\d{4})\b",
    re.IGNORECASE,
)

AFFIRMATIVE_CONFIRMATION_PATTERN = re.compile(
    r"^\s*(?:yes|y|confirm|confirmed|correct|that's correct)\s*[.!]?\s*$",
    re.IGNORECASE,
)

NEGATIVE_CONFIRMATION_PATTERN = re.compile(
    r"^\s*(?:no|n|incorrect|that's incorrect)\s*[.!]?\s*$",
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

    content = user_message.text
    valid_ids = set(VALID_INCIDENT_ID_PATTERN.findall(content))

    if len(valid_ids) == 1:
        return {
            "authorized_incident_id": next(iter(valid_ids)),
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": False,
        }

    if len(valid_ids) > 1:
        return {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": True,
        }

    if (
        state.pending_incident_id_confirmation is not None
        and AFFIRMATIVE_CONFIRMATION_PATTERN.fullmatch(content)
    ):
        return {
            "authorized_incident_id": (state.pending_incident_id_confirmation),
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": False,
        }

    if (
        state.pending_incident_id_confirmation is not None
        and NEGATIVE_CONFIRMATION_PATTERN.fullmatch(content)
    ):
        return {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": True,
        }

    candidate_match = UNPREFIXED_INCIDENT_ID_PATTERN.search(content)

    if candidate_match is not None:
        candidate_id = f"INC-{candidate_match.group(1)}"

        return {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": candidate_id,
            "is_incident_id_input_invalid": True,
        }

    content_without_valid_ids = VALID_INCIDENT_ID_PATTERN.sub("", content)

    if MALFORMED_INCIDENT_REFERENCE_PATTERN.search(content_without_valid_ids):
        return {
            "authorized_incident_id": None,
            "pending_incident_id_confirmation": None,
            "is_incident_id_input_invalid": True,
        }

    return {}
