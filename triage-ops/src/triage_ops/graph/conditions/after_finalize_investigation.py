from typing import Literal

from langgraph.graph import END

from triage_ops.domain.investigation import (
    ExecutableProposal,
    InvestigationResult,
)
from triage_ops.graph import State
from triage_ops.graph.nodes import Nodes


def after_finalize_investigation(
    state: State,
) -> Literal[Nodes.PREPARE_APPROVALS, "__end__"]:
    result = state.final_result

    if not isinstance(result, InvestigationResult):
        return END

    has_executable_actions = any(
        isinstance(action, ExecutableProposal) for action in result.recommended_actions
    )

    if not has_executable_actions:
        return END

    return Nodes.PREPARE_APPROVALS
