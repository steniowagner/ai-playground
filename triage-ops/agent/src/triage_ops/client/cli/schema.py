from dataclasses import dataclass

from triage_ops.graph import GraphRunner
from triage_ops.graph.event_stream import (
    ApprovalRequiredEvent,
)


@dataclass(frozen=True, slots=True)
class HandleApprovalRequiredEventArgs:
    graph_runner: GraphRunner
    thread_id: str
    event: ApprovalRequiredEvent
