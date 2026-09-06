from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationResponse,
)
from incident_triage_assistant_langchain.state import State
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable

from .prompts import FINALIZER_HUMAN_PROMPT, FINALIZER_SYSTEM_PROMPT


def finalize_investigation_node(
    state: State,
    *,
    model: Runnable[LanguageModelInput, InvestigationResponse],
) -> dict:
    evidence_messages = state.messages[:-1]

    structured_response = model.invoke(
        [
            SystemMessage(content=FINALIZER_SYSTEM_PROMPT),
            *evidence_messages,
            HumanMessage(content=FINALIZER_HUMAN_PROMPT),
        ]
    )

    return {"final_result": structured_response.outcome}
