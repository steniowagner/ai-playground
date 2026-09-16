from typing import Literal

from triage_ops.graph.nodes.check_scope.schema import RequestScope
from triage_ops.graph.nodes.schema import Nodes
from triage_ops.graph.state import State


def after_scope_check(
    state: State,
) -> Literal[Nodes.LLM_CALL, Nodes.REJECT_OUT_OF_SCOPE]:
    if state.request_scope == RequestScope.IN_SCOPE:
        return Nodes.LLM_CALL

    return Nodes.REJECT_OUT_OF_SCOPE
