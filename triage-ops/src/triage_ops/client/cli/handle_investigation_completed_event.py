from triage_ops.graph.event_stream.schema import (
    InvestigationCompletedEvent,
)


def handle_investigation_completed_event(event: InvestigationCompletedEvent) -> None:
    print("\n[Investigation Completed]\n")
    print(event.result.model_dump_json(indent=2))
