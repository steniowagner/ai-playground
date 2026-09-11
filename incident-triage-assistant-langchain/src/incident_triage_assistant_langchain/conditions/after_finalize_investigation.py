from typing import Literal

from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.investigation.schema import (
    ExecutableProposal,
    InvestigationResult,
)
from incident_triage_assistant_langchain.nodes.schema import Nodes
from langgraph.graph import END


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
