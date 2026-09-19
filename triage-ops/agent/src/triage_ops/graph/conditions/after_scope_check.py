from typing import Literal

from triage_ops.graph import State
from triage_ops.graph.nodes import Nodes
from triage_ops.graph.nodes.check_scope import RequestScope


def after_scope_check(
    state: State,
) -> Literal[Nodes.LLM_CALL, Nodes.REJECT_OUT_OF_SCOPE]:
    if state.request_scope == RequestScope.IN_SCOPE:
        return Nodes.LLM_CALL

    return Nodes.REJECT_OUT_OF_SCOPE
