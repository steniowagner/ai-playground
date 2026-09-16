from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable

from triage_ops.domain.investigation import (
    InvestigationResponse,
)
from triage_ops.domain.investigation.exceptions import InvalidInvestigationResponse
from triage_ops.graph import State

from .prompts import FINALIZER_HUMAN_PROMPT, FINALIZER_SYSTEM_PROMPT
from .utils import build_evidence_transcript


def finalize_investigation_node(
    state: State,
    *,
    model: Runnable[LanguageModelInput, InvestigationResponse],
) -> dict:
    if state.authorized_incident_id is None:
        raise InvalidInvestigationResponse(
            "An investigation cannot be finalized without an authorized incident."
        )

    evidence_transcript = build_evidence_transcript(state)

    structured_response = model.invoke(
        [
            SystemMessage(content=FINALIZER_SYSTEM_PROMPT),
            HumanMessage(content=f"{evidence_transcript}\n\n{FINALIZER_HUMAN_PROMPT}"),
        ]
    )

    if structured_response.outcome.incident_id != state.authorized_incident_id:
        raise InvalidInvestigationResponse(
            "The finalized incident does not match the authorized incident."
        )

    return {
        "final_result": structured_response.outcome,
        "pending_approvals": [],
        "approval_decisions": [],
        "is_incident_id_input_invalid": True,
        "authorized_incident_id": None,
    }
