# Graph integration tests

These tests exercise the compiled LangGraph application with an
`InMemorySaver`, scripted model responses, and in-process repository and service
test doubles. They do not contact model providers, external services, or the
network.

The integration suite protects these workflow guarantees:

- out-of-scope, greeting, ordinary lookup, and incident-ID validation paths;
- incident authorization and blocking of unauthorized incident access;
- successful, unknown, retryable, exhausted-retry, and non-retryable
  investigations;
- safe degradation when supporting evidence is unavailable;
- one approval per executable proposal, with advisory actions excluded;
- approved-only execution, deterministic proposal order, rejection safety, and
  exactly-once service calls;
- safe service-failure events without leaking internal exception details;
- strict resume validation that cannot execute malformed approval decisions;
- multi-turn history without duplicated messages or stale investigation state;
- checkpoint isolation for interleaved thread IDs.

Run only this suite with:

```bash
uv run pytest -m integration
```

Run it as part of the deterministic coverage gate with the command documented
in [`tests/README.md`](../README.md).
