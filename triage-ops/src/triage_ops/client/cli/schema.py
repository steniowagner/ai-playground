from dataclasses import dataclass

from triage_ops.graph.event_stream.schema import (
    ApprovalRequiredEvent,
)
from triage_ops.graph.runner import GraphRunner


@dataclass(frozen=True, slots=True)
class HandleApprovalRequiredEventArgs:
    graph_runner: GraphRunner
    thread_id: str
    event: ApprovalRequiredEvent
