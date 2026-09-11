from typing import Literal

from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.state import State
from langgraph.graph import END


def after_finalize_investigation(
    state: State,
) -> Literal[Nodes.PREPARE_APPROVALS, "__end__"]:
    return Nodes.PREPARE_APPROVALS if state.final_result.recommended_actions else END
