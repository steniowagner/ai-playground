from langchain.messages import SystemMessage
from langchain_core.language_models import (
    LanguageModelInput,
)
from langchain_core.messages import (
    AIMessage,
)
from langchain_core.runnables import Runnable
from triage_ops.graph.state import State

from .prompts import SYSTEM_PROMPT


def llm_call_node(
    state: State, *, model: Runnable[LanguageModelInput, AIMessage]
) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if state.pending_incident_id_confirmation is not None:
        messages.append(
            SystemMessage(
                content=(
                    "The deterministic input validator identified "
                    f"{state.pending_incident_id_confirmation} as a possible "
                    "incident ID, but it is not authorized yet. Ask the user "
                    "to confirm that exact ID. Do not call incident tools "
                    "until confirmation is recorded."
                )
            )
        )

    messages.extend(state.messages)

    return {"messages": [model.invoke([*messages, *state.messages])]}
