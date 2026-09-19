# Public event-stream contract notes

The event stream is the public boundary between LangGraph execution and clients
such as the CLI. Tests assert event semantics rather than terminal formatting.

## Public event identity and ordering

- Every event emitted by `parse_graph_event` receives its own UUID, including
  multiple events derived from one graph update.
- The caller-provided thread ID is copied to every event.
- `GraphRunner` preserves the order in which LangGraph supplies message, custom,
  and update payloads.
- One update preserves its internal order: investigation completion first,
  followed by proposal records in state order.

## Proposal lifecycle

- Approval interrupts become `ApprovalRequiredEvent`.
- `executing` records become `ExecutingProposalEvent`.
- `executed`, `failed`, and `rejected` records become
  `ProposalExecutionFinishedEvent`.
- Successful and failed records contain their safe serialized service response.
  Rejected records contain `result=None` because no mutation was attempted.
- `pending` and `approved` records do not emit execution lifecycle events.

## Parser robustness

Unknown modes, irrelevant updates, malformed message tuples, incomplete custom
events, malformed interrupts, invalid final results, and invalid approval
entries are ignored. They do not produce partial public events and do not crash
the stream parser.

Internal scope and finalizer model chunks remain hidden. Tool lifecycle events
expose only their public tool name, arguments, status, and safe error code; they
do not include internal exceptions.
