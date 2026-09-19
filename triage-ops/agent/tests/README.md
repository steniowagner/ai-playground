# Test suite

Tests are grouped by application module rather than mirroring every source file:

- `domain/`
- `repositories/`
- `tools/`
- `services/`
- `graph/`
- `event_stream/`
- `integration/`
- `cli/`
- `evaluations/`

Shared object factories and test doubles live in `support/`. Tests must not make
real model-provider or network calls; the global fixture in `conftest.py` blocks
socket connections so accidental external calls fail immediately.

Run the deterministic suite with enforced branch coverage and terminal/XML
reports with:

```bash
uv run pytest --cov=triage_ops --cov-branch --cov-report=term-missing --cov-report=xml
```

The coverage gate starts at 89%, just below the measured 89.95% baseline. The
threshold lives in `pyproject.toml`; raise it as the remaining CLI and model
paths gain deterministic tests. The XML report is written to `coverage.xml`.

For a quick test run without collecting coverage, use:

```bash
uv run pytest
```

Useful selections:

```bash
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m evaluation
uv run pytest -m "not slow and not evaluation"
```

Model evaluations are excluded from the default run. Their development and
held-out acceptance thresholds are documented in `evaluations/README.md`.
