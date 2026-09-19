# Graph safety contract notes

The graph tests define which decisions may be influenced by a model and which
must remain deterministic application controls.

## Incident authorization

- User input parsing is deterministic. Models cannot authorize, normalize, or
  construct incident IDs.
- `get_incident` and `complete_investigation` may use only the exact currently
  authorized ID.
- A finalizer response must target that same authorized incident. Missing
  authorization or a cross-incident response raises
  `InvalidInvestigationResponse` before state is finalized.

## Tool execution

- Calls are validated, executed, and returned in model-supplied order.
- An invalid or unknown call produces a safe tool result without preventing an
  independent valid call later in the same batch.
- Identical successful calls and non-retryable failures cannot be repeated. One
  retry is allowed only after a retryable failure.
- Tool output, including instruction-like text, remains untrusted evidence and
  is never inserted into a system prompt.

## Approval and mutation boundary

- Only executable proposals create approval records; advisory actions never do.
- Resume payloads must provide exactly one decision for every pending proposal.
  Proposal IDs must match and `approved` must be a real JSON boolean—coerced
  strings and integers are rejected.
- Only records explicitly marked `approved` transition to execution. Pending,
  rejected, executed, and failed records are never executed again.
- Unknown services, invalid arguments, and service execution failures become
  safe standard error responses without exposing internal exception details.

## Routing and state

All conditional routes have deterministic decision-table tests. Integration
tests compile the real graph with an in-memory checkpointer and cover ordinary
answers, incident investigation, retry behavior, finalization, interruption,
approval, rejection, execution, and thread isolation without a real model or
external API.
