from incident_triage_assistant_langchain.prompts import SYSTEM_PROMPT
from incident_triage_assistant_langchain.state import State
from langchain.messages import SystemMessage
from langchain_core.language_models import (
    LanguageModelInput,
)
from langchain_core.messages import (
    AIMessage,
)
from langchain_core.runnables import Runnable


def llm_call_node(
    state: State, *, model_with_tools: Runnable[LanguageModelInput, AIMessage]
) -> dict:
    return {
        "messages": [
            model_with_tools.invoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + state.messages
            )
        ]
    }
