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
