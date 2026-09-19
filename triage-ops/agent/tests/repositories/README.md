# Repository contract test notes

The repository tests define the storage-facing contract. They deliberately stop
at the boundary where a tool turns repository records into a user-facing tool
response.

## Shared fixture behavior

- Missing files or directories raise `RepositoryUnavailable` and are retryable.
- Invalid JSON, invalid UTF-8, and schema-invalid records raise
  `RepositoryDataError` and are not retryable.
- Empty, valid fixtures load as empty datasets. Public lookup methods then return
  `None` for singular lookups or `[]` for collection lookups.
- Fixture-only incident truth is removed before an incident leaves the
  repository.

## Layer-boundary decisions

### Deployments

The repository returns every deployment matching the exact service,
environment, and half-open overlap window. It sorts matches by completion time,
newest first. There is no implicit repository result limit because neither the
repository nor tool contract exposes one. If a production data source requires
pagination or a cap, that must become an explicit contract rather than silently
truncating evidence.

### Metrics

The repository filters complete metric records by exact service, environment,
and the inclusive time range, then returns them chronologically. Selection of
requested metric fields, construction of metric series, aggregation into the
tool result, and reporting unavailable series belong to `QueryMetricsTool`.
Keeping those responsibilities there lets the repository preserve a complete
record while the tool owns its response schema.

### Maintenance windows

The repository returns every non-cancelled window that overlaps the requested
half-open interval, regardless of whether its status is `scheduled`,
`in_progress`, or `completed`. The caller can distinguish past, active, and
future windows using status and timestamps. Cancelled windows are excluded.

### Runbooks

Runbook Markdown is untrusted repository data. The repository retrieves exact
content without interpreting or executing instruction-like text. Consumers are
responsible for treating that content as evidence rather than authority.
