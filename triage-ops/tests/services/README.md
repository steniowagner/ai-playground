# Service contract test notes

The service tests define the boundary between approved executable proposals and
operational side effects.

## Arguments and results

- Every service accepts its own validated, immutable Pydantic argument model.
  Untyped mappings are rejected rather than being accepted implicitly.
- Argument schemas reject unknown fields, unsupported enum values, malformed
  incident IDs, and empty identifiers.
- Successful services return `ServiceSuccessResponse` with the exact arguments
  serialized to JSON-compatible data. This keeps every action result the same
  shape.

## Failure ownership

An unexpected failure while performing an operation is wrapped in
`ServiceExecutionException` with a safe action-specific message. The original
exception remains available as the cause for internal diagnostics, but its
details are not copied into the public service response.

The approval-execution graph owns conversion of `ServiceExecutionException`
into the standard `EXECUTION_ERROR` response. Argument construction and schema
validation happen before an operation is attempted.

## Registry

`bootstrap_services()` maps every executable proposal discriminator to exactly
one service. Advisory proposals are intentionally absent because they describe
human follow-up and are never executed.
