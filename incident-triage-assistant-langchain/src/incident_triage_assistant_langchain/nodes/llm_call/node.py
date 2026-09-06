from incident_triage_assistant_langchain.state import State
from langchain.messages import SystemMessage
from langchain_core.language_models import (
    LanguageModelInput,
)
from langchain_core.messages import (
    AIMessage,
)
from langchain_core.runnables import Runnable

from .prompts import SYSTEM_PROMPT


def llm_call_node(
    state: State, *, model: Runnable[LanguageModelInput, AIMessage]
) -> dict:
    return {
        "messages": [
            model.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state.messages)
        ]
    }
