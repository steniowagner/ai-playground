# Known limitations

This repository is a learning implementation, not a production incident-management system.

## Model behavior

- Prompt instructions cannot guarantee ideal investigation depth. Structured-result validation catches some premature answers, but semantic quality still requires evaluation.
- The incomplete-investigation validator uses a small phrase list and is not a general semantic judge.
- A valid JSON result may still contain a weak inference. Pydantic validates structure, not factual reasoning quality.
- Tool-call and invalid-result retries are bounded, but retrying does not guarantee that the provider will produce a corrected response.

## Safety and actions

- All implemented tools are read-only.
- Rollback, restart, feature-flag mutation, escalation, and other operational actions are not implemented.
- Human approval was designed conceptually but is not part of this milestone. A production design must bind approval to exact normalized action parameters, make approval single-use, and keep approval decisions outside LLM control.
- The top-level `requires_human_approval` value is model-generated and can theoretically contradict individual recommended actions. A future version should derive it or enforce consistency.

## State and persistence

- Conversation history exists only for the current process.
- Investigations, approvals, decisions, and execution results are not persisted.
- There is no resume-after-restart support or multi-user isolation.

## Data and integrations

- Incidents, services, logs, metrics, deployments, feature flags, maintenance windows, and runbooks are fictional local fixtures.
- There are no integrations with production observability, incident-management, deployment, or feature-flag systems.
- Fixture repositories read files directly and are appropriate for this project size, not high-volume telemetry.

## Operations

- The interface is a synchronous terminal loop.
- FastAPI, authentication, authorization, audit logging, tracing, and distributed execution are not implemented.
- Configuration is environment-based and assumes valid values are supplied.
- Provider-specific capabilities and tool-calling behavior may vary by selected Groq model.

## Evaluation

- The fixture data contains hidden truth for learning and future evaluation, but there is no automated end-to-end quality evaluation harness yet.
- Unit tests cover schemas, repositories, tools, history, provider-error mapping, retries, and orchestration boundaries. They do not measure root-cause accuracy, evidence completeness, or action quality across live model runs.

These are conscious stopping points. They do not block the project’s purpose: learning the mechanics of a tool-using agent before moving to a framework-oriented course.
