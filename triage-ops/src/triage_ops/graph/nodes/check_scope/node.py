from langchain.messages import SystemMessage
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable

from triage_ops.graph import State

from ..utils import get_latest_user_message
from .prompts import SCOPE_PROMPT
from .schema import ScopeDecision


def check_scope_node(
    state: State,
    *,
    model: Runnable[LanguageModelInput, ScopeDecision],
) -> dict:
    user_message = get_latest_user_message(state)
    if user_message is None:
        return {}

    decision = model.invoke(
        [
            SystemMessage(content=SCOPE_PROMPT),
            user_message,
        ]
    )

    return {"request_scope": decision.scope}
