from collections.abc import Iterable
from uuid import uuid4

from .parse_custom_event import parse_custom_event
from .parse_message_event import parse_message_event
from .parse_update_event import parse_update_event
from .schema import Event, GraphEvent, ParseGraphEventArgs


def parse_graph_event(args: ParseGraphEventArgs) -> Iterable[GraphEvent]:
    base_event_args = Event(event_id=uuid4(), thread_id=args.thread_id)

    if args.mode == "messages":
        event = parse_message_event(args.payload, base_event_args)
        return [event] if event is not None else []

    if args.mode == "custom":
        event = parse_custom_event(args.payload, base_event_args)
        return [event] if event is not None else []

    if args.mode == "updates":
        return parse_update_event(args.payload, base_event_args)

    return []
