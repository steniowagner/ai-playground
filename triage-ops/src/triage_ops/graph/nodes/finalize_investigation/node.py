from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable

from triage_ops.domain.investigation import (
    InvestigationResponse,
)
from triage_ops.graph import State

from .prompts import FINALIZER_HUMAN_PROMPT, FINALIZER_SYSTEM_PROMPT
from .utils import build_evidence_transcript


def finalize_investigation_node(
    state: State,
    *,
    model: Runnable[LanguageModelInput, InvestigationResponse],
) -> dict:
    evidence_transcript = build_evidence_transcript(state)

    structured_response = model.invoke(
        [
            SystemMessage(content=FINALIZER_SYSTEM_PROMPT),
            HumanMessage(content=f"{evidence_transcript}\n\n{FINALIZER_HUMAN_PROMPT}"),
        ]
    )

    return {
        "final_result": structured_response.outcome,
        "pending_approvals": [],
        "approval_decisions": [],
        "is_incident_id_input_invalid": True,
        "authorized_incident_id": None,
    }
