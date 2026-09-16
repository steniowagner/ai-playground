from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .parse_graph_event import parse_graph_event
    from .schema import (
        ApprovalRequiredEvent,
        BaseProposalEvent,
        BaseToolEvent,
        CustomStreamEvents,
        ExecutingProposalEvent,
        GraphEvent,
        InvestigationCompletedEvent,
        MessageChunkEvent,
        ModelThinkingEvent,
        ParseGraphEventArgs,
        ProposalExecutionFinishedEvent,
        ToolFailedEvent,
        ToolFinishedEvent,
        ToolSkippedEvent,
        ToolStartedEvent,
    )

__all__ = [
    "ApprovalRequiredEvent",
    "BaseProposalEvent",
    "BaseToolEvent",
    "CustomStreamEvents",
    "ExecutingProposalEvent",
    "GraphEvent",
    "InvestigationCompletedEvent",
    "MessageChunkEvent",
    "ModelThinkingEvent",
    "ParseGraphEventArgs",
    "ProposalExecutionFinishedEvent",
    "ToolFailedEvent",
    "ToolFinishedEvent",
    "ToolSkippedEvent",
    "ToolStartedEvent",
    "parse_graph_event",
]

_EXPORTS = {
    "parse_graph_event": (".parse_graph_event", "parse_graph_event"),
    "ApprovalRequiredEvent": (".schema", "ApprovalRequiredEvent"),
    "BaseProposalEvent": (".schema", "BaseProposalEvent"),
    "BaseToolEvent": (".schema", "BaseToolEvent"),
    "CustomStreamEvents": (".schema", "CustomStreamEvents"),
    "ExecutingProposalEvent": (".schema", "ExecutingProposalEvent"),
    "GraphEvent": (".schema", "GraphEvent"),
    "InvestigationCompletedEvent": (".schema", "InvestigationCompletedEvent"),
    "MessageChunkEvent": (".schema", "MessageChunkEvent"),
    "ModelThinkingEvent": (".schema", "ModelThinkingEvent"),
    "ParseGraphEventArgs": (".schema", "ParseGraphEventArgs"),
    "ProposalExecutionFinishedEvent": (".schema", "ProposalExecutionFinishedEvent"),
    "ToolFailedEvent": (".schema", "ToolFailedEvent"),
    "ToolFinishedEvent": (".schema", "ToolFinishedEvent"),
    "ToolSkippedEvent": (".schema", "ToolSkippedEvent"),
    "ToolStartedEvent": (".schema", "ToolStartedEvent"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from error

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
