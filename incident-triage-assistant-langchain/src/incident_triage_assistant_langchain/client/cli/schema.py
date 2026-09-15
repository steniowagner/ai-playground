from dataclasses import dataclass

from incident_triage_assistant_langchain.graph.event_stream.schema import (
    ApprovalRequiredEvent,
)
from incident_triage_assistant_langchain.graph.runner import GraphRunner


@dataclass(frozen=True, slots=True)
class HandleApprovalRequiredEventArgs:
    graph_runner: GraphRunner
    thread_id: str
    event: ApprovalRequiredEvent
