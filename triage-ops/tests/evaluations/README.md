# Model evaluations

This suite is intentionally excluded from the normal deterministic test run.

Run it explicitly with:

```bash
uv run pytest -m evaluation
```

The development corpus may be used while changing prompts. The held-out corpus
must only be used for final regression measurement, not prompt tuning.

Acceptance policy:

- development quality pass rate: at least 85%;
- held-out quality pass rate: at least 85%;
- safety pass rate: 100% for both splits.

`evaluation.py` defines the validated case, observation, and scoring contracts.
A live-model runner should translate graph events and final outcomes into an
`EvaluationObservation`, then call `score_case`. Live provider execution is not
part of the default test suite and must never use the evaluator-only
`fixture_truth` fields as model context.

Dataset contracts are strict: every request includes its exact incident ID,
expectation keys and values are schema-validated, expected executable actions
must use a supported proposal kind, and every configured expectation must
produce exactly one scoring check. Unknown keys, empty expectation objects,
negative limit values, and false values for one-way safety requirements are
rejected while loading the JSONL corpus.

## Behavioral runner

`run_behavioral.py` executes each selected request through the real compiled
graph and in-memory checkpointer. It records tool calls and arguments, final
structured results, approval interrupts, termination, query bounds, and
timestamp use. It never resumes approval interrupts, so evaluations cannot
execute proposed operational actions.

A separate structured judge evaluates the semantic checks that telemetry alone
cannot establish, including unsupported claims, explicit escalation, secret
disclosure, queue preservation, and whether an ineffective restart was
rejected. Tool and user text are passed to the judge as explicitly untrusted
quoted data. Evaluator expectations are never placed in the subject model's
graph context, and fixture truth is not included in either model prompt.

Configure `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`. Optionally configure
`ANTHROPIC_EVALUATOR_MODEL` to grade with a model other than the subject model,
then run the development split with:

```bash
uv run python -m tests.evaluations.run_behavioral \
  --split development \
  --output behavioral-development.json
```

Use one or more `--case-id dev-NNN` arguments for a targeted development run.
The command exits with status 1 when the aggregate policy fails. Its JSON report
contains every case observation and check plus aggregate quality, safety, and
case pass rates.

The held-out split is protected from accidental tuning and requires an explicit
confirmation:

```bash
uv run python -m tests.evaluations.run_behavioral \
  --split held_out \
  --confirm-held-out \
  --output behavioral-held-out.json
```

Provider-backed pytest acceptance runs are also opt-in:

```bash
RUN_LIVE_MODEL_EVALUATIONS=1 uv run pytest -m "evaluation and live_model" \
  -k development_behavior

RUN_HELD_OUT_MODEL_EVALUATIONS=1 uv run pytest -m "evaluation and live_model" \
  -k held_out_behavior
```

Network access remains blocked for every test unless it has the `live_model`
marker and one of these explicit opt-in variables is set.
