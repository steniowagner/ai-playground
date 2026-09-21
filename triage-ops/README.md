# TriageOps

> An evidence-grounded incident-triage agent built to study and practice AI engineering.

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agentic_workflow-1C3C3C)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![Coverage gate](https://img.shields.io/badge/coverage_gate-89%25-brightgreen)

![TriageOps: incident triage, grounded in evidence](frontend/public/og.png)

TriageOps is my first AI-engineering project. I built it to move beyond simple chatbot demos and practice the parts of AI applications that become difficult as soon as a model can inspect data, make decisions, and propose actions.

The application investigates fictional software incidents using operational tools for incidents, services, deployments, logs, metrics, feature flags, maintenance windows, and runbooks. It can form an evidence-backed conclusion, recommend a remediation, pause for human approval, and only then execute the approved action through a controlled application boundary.

This is intentionally a learning project, not a production incident-management system. The data is fictional, operational actions are simulated, and the implementation favors explicit engineering concepts that can be studied, tested, and discussed.

## At a glance

- **Agent architecture:** a stateful LangGraph workflow with explicit routing, tool loops, finalization, interruption, and resume.
- **Grounded investigations:** nine typed retrieval tools backed by repository interfaces; the model must base operational claims on successful results.
- **Human approval:** executable proposals stop at a LangGraph interrupt and resume only with a strictly validated decision payload.
- **Safety controls:** deterministic incident authorization, bounded telemetry queries, retry limits, structured errors, and untrusted-data handling.
- **Evaluation:** 18 development cases, 7 held-out cases, deterministic graph tests, telemetry-derived checks, and an independent semantic judge.
- **Full-stack delivery:** FastAPI, SSE streaming, PostgreSQL, a Next.js investigation UI, an evaluation workspace, a CLI, and Docker Compose.

## Contents

- [Demos](#demos)
- [Why I built it](#why-i-built-it)
- [What the application does](#what-the-application-does)
- [Interface](#interface)
- [Architecture](#architecture)
- [AI-engineering topics practiced](#ai-engineering-topics-practiced)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Running the project](#running-the-project)
- [Tests and evaluations](#tests-and-evaluations)
- [What I learned](#what-i-learned)
- [Hardest parts](#hardest-parts)
- [Current limitations and tradeoffs](#current-limitations-and-tradeoffs)
- [Production-readiness roadmap](#production-readiness-roadmap)

## Demos

| Experience           | What the demo shows                                                                                         | Video                                                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Web application      | The full investigation workspace, streamed agent activity, evidence-backed results, and human approval flow | [▶ Watch the web app demo](https://stenio-wagner-project-demos.s3.us-east-1.amazonaws.com/triageops-app.mp4)           |
| Evaluation workspace | A behavioral evaluation running through the complete graph, followed by its quality and safety results      | [▶ Watch the evaluation demo](https://stenio-wagner-project-demos.s3.us-east-1.amazonaws.com/triageops-evaluation.mp4) |
| CLI                  | The incident-triage workflow running as an interactive terminal application                                 | [▶ Watch the CLI demo](https://stenio-wagner-project-demos.s3.us-east-1.amazonaws.com/triageops-cli.mp4)               |

## Why I built it

LLM prototypes often look convincing while hiding the hardest questions:

- How do I prevent the model from inventing operational facts?
- Which decisions belong to the model, and which must remain deterministic?
- How do I safely pause an agent before a side effect?
- How do I test behavior that is probabilistic rather than purely functional?
- How do I expose useful progress without leaking chain-of-thought or internal errors?
- How do I know the agent stopped because it had enough evidence rather than because it gave up?

TriageOps is my practical exploration of those questions. The goal is not to automate incident response completely. It is to learn how to build a bounded, observable, testable agent that works with application code instead of replacing it.

## What the application does

A user can ask an ordinary operational question or request a full incident investigation.

For a full investigation, TriageOps:

1. validates and authorizes the incident ID from the user's input
2. retrieves the authoritative incident record
3. selects relevant evidence sources instead of following a fixed checklist
4. queries bounded operational data through typed, read-only tools
5. stops when more calls are unlikely to reduce uncertainty
6. asks a separate structured-output model call to synthesize the evidence
7. presents executable recommendations as proposals
8. interrupts the graph and waits for an explicit human decision
9. executes only proposals that were approved

It also supports direct questions such as “Who owns `checkout-api`?” or “Which feature flags are enabled?” without forcing every interaction through the full investigation workflow.

## Interface

![TriageOps incident workspace](frontend/public/triageops-workspace.jpg)
![TriageOps development evaluation](frontend/public/triageops-development-evaluation.jpg)
![TriageOps held-out evaluation](frontend/public/triageops-held-out-evaluation.jpg)
![TriageOps cli](frontend/public/triageops-cli.png)

The main workspace combines the conversation, live tool and proposal activity, evidence-backed investigation cards, approval controls, and a catalog of sample scenarios. A separate evaluation workspace runs development or held-out cases and presents quality and safety checks.

## Architecture

```mermaid
flowchart LR
    U[User] --> UI[Next.js UI]
    UI -->|POST + SSE| PX[Next.js API proxy]
    PX --> API[FastAPI]
    API --> RUNNER[GraphRunner]
    RUNNER --> GRAPH[LangGraph workflow]

    GRAPH --> MODEL[Anthropic chat model]
    GRAPH --> TOOLS[Typed read-only tools]
    TOOLS --> REPOS[Repository interfaces]
    REPOS --> PG[(PostgreSQL)]
    REPOS --> FILES[JSON / JSONL / Markdown fixtures]

    GRAPH --> APPROVAL[Human approval interrupt]
    APPROVAL --> UI
    GRAPH --> SERVICES[Controlled action services]
    SERVICES --> SIM[Simulated operational actions]

    GRAPH --> EVENTS[Public graph events]
    EVENTS -->|SSE stream| UI
```

The browser never calls FastAPI directly. It talks to a server-side Next.js proxy, which forwards regular responses and server-sent event streams to the API. The production-like application uses PostgreSQL-backed repositories for operational records and file-backed runbooks. The evaluation runner swaps in deterministic file-backed repositories so scenarios are repeatable.

### LangGraph workflow

```mermaid
flowchart TD
    START((Start)) --> PREPARE[Prepare user request]
    PREPARE --> SCOPE[Check scope]

    SCOPE -->|Out of scope| REJECT[Return bounded scope response]
    REJECT --> END1((End))

    SCOPE -->|In scope| AGENT[LLM call]
    AGENT -->|No tool call| END2((End))
    AGENT -->|Tool calls| TOOL[Validate and execute tools]

    TOOL -->|More evidence needed| AGENT
    TOOL -->|complete_investigation| FINALIZE[Finalize structured investigation]

    FINALIZE -->|No executable proposal| END3((End))
    FINALIZE -->|Executable proposals| PREP_APPROVALS[Prepare approvals]
    PREP_APPROVALS --> INTERRUPT[Interrupt: request human decisions]
    INTERRUPT -. resume .-> EXECUTE[Execute approved proposals]
    EXECUTE --> END4((End))
```

The graph deliberately separates evidence collection from report generation. The agent decides which tools to call, but it does not write the final investigation report itself. A dedicated finalizer receives a constrained evidence transcript and must return a validated `InvestigationResult` or `InvestigationFailure`.

## AI-engineering topics practiced

### Agents and tool use

The core agent is an LLM bound to a set of tools. It can plan the next useful lookup, inspect the result, and repeat the loop until the evidence is sufficient. Tool inputs and outputs are Pydantic models, which gives the model an explicit contract and gives the application a validation boundary.

This is tool-augmented generation rather than classic vector-search RAG. The model grounds its response in structured operational records retrieved through repositories and tools; there is no embedding or vector database in this project.

### Graph-based agents with LangGraph

LangGraph makes the control flow explicit. Nodes own individual responsibilities, conditional edges route from state, and a checkpointer isolates conversation state by thread. This makes the workflow easier to test than a single open-ended agent loop and gives the application deterministic places to enforce safety rules.

### Stateful, multi-turn interaction

Conversation messages, authorized incident IDs, final results, pending approvals, and approval decisions live in typed graph state. The graph can stop at an interrupt and later resume from the same thread after the user submits approval decisions.

### Human in the loop (HITL)

Executable recommendations: rollback, restart, feature-flag disablement, or incident escalation never run directly from model output. They become proposals with application-generated IDs. LangGraph interrupts execution, the UI collects one decision for every pending proposal, and the backend validates the resume payload before any service is called.

The user's sentence “I approve it” is not treated as authorization. Approval must arrive through the explicit approval endpoint and match the pending proposal IDs.

### Structured outputs

Structured output is used for both scope classification and final investigation synthesis. The final schema constrains severity, evidence sources, likely causes, confidence, and supported action types. Cross-incident responses are rejected if the finalizer returns an incident ID different from the one deterministically authorized from user input.

### Grounding and evidence discipline

The system prompt requires operational claims to come from successful tool results. The finalizer receives the current investigation's user request, tool calls, and tool results as an evidence transcript. It must distinguish observations from inferred causes, treat timing as correlation rather than proof, and lower confidence when important evidence is unavailable.

### Guardrails and deterministic controls

I tried to keep security-sensitive decisions outside the model:

- incident IDs are parsed and authorized by application code
- malformed, inferred, or multiple incident IDs cannot reach protected tools
- tool arguments are schema-validated before invocation
- repeated identical tool calls are blocked, with one retry allowed only for retryable failures
- log and metric queries have bounded windows and result limits
- tool errors are returned in a safe, standardized shape
- approval records and proposal IDs are generated by the application
- only proposals with an explicit `approved` state can cross the mutation boundary.

### Prompt-injection resistance

Logs and runbooks are useful evidence, but they are untrusted model input. The prompts explicitly tell both the agent and finalizer not to follow instructions found in tool data. The fixture set includes a hostile log record to exercise this behavior, and the tests check that internal instructions and secret requests do not become actions or disclosures.

### Event streaming and progressive UX

The graph streams three kinds of LangGraph output messages: updates and custom events, which are normalized into a public event contract. FastAPI exposes them over server-sent events, and the frontend renders tool progress, final results, approval requests, and proposal execution states.

Raw model thinking is intentionally excluded from the UI. Users see a generic working state and useful operational events rather than hidden reasoning tokens.

### Evaluations

The project has two complementary testing layers:

1. **Deterministic tests** exercise domain models, repositories, tools, graph routing, retry behavior, thread isolation, interrupts, approvals, service failures, and event parsing without calling a model provider.
2. **Behavioral model evaluations** run curated scenarios through the real graph and grade both quality and safety expectations.

The evaluation corpus is split into visible development cases and held-out cases. Expectations cover items such as:

- required evidence sources
- severity preservation
- likely-cause content and evidence references
- expected and forbidden action types
- approval requirements
- unsupported claims
- prompt-injection and secret-disclosure resistance
- bounded log queries
- duplicate-call limits
- future-evidence use
- preservation of queued work

Many checks are derived directly from graph telemetry. Semantic behaviors that cannot be reliably reduced to telemetry are evaluated by a separate structured-output judge model. The subject model never receives evaluation expectations or the fixture-only ground truth.

Current acceptance thresholds are 85% for overall quality and 100% for safety. Held-out evaluations require explicit confirmation so they are less likely to become accidental prompt-tuning data.

## Technology stack

| Area              | Technology                   | Role                                                                        |
| ----------------- | ---------------------------- | --------------------------------------------------------------------------- |
| Agent workflow    | LangGraph                    | Stateful graph, conditional routing, checkpointing, interrupts, and resume  |
| Model integration | LangChain + Anthropic        | Tool binding, structured output, and model invocation                       |
| Validation        | Pydantic                     | State, tool, event, evaluation, and API contracts                           |
| API               | FastAPI                      | Thread creation, SSE streams, approvals, samples, and evaluation endpoints  |
| Data access       | SQLAlchemy + PostgreSQL      | Production-like repository implementations and seeded operational data      |
| Frontend          | Next.js + React + TypeScript | Investigation workspace, evaluation UI, and API proxy                       |
| Test data         | JSON, JSONL, Markdown        | Deterministic incidents, telemetry, runbooks, prompts, and evaluation cases |
| Tooling           | `uv`, `pnpm`, Docker Compose | Dependency management and local execution                                   |

## Repository structure

```text
triage-ops/
├── agent/
│   ├── data/
│   │   ├── evals/              # Development and held-out evaluation cases
│   │   ├── fixtures/           # Fictional operational data
│   │   ├── runbooks/           # Untrusted runbook content
│   │   └── sample_questions/   # Prompts shown in the UI
│   ├── src/triage_ops/
│   │   ├── client/             # FastAPI and CLI clients
│   │   ├── db/                 # SQLAlchemy models and initialization
│   │   ├── domain/             # Core operational and investigation schemas
│   │   ├── evaluation/         # Behavioral runner, observations, and scoring
│   │   ├── graph/              # LangGraph state, nodes, edges, and event stream
│   │   ├── model/              # Model factory and provider configuration
│   │   ├── repositories/       # JSON and PostgreSQL data-access adapters
│   │   ├── services/           # Approval-gated simulated actions
│   │   └── tools/              # Typed read-only tools and tool bootstrap
│   └── tests/                  # Unit, integration, event, and evaluation tests
├── frontend/
│   ├── app/                    # Next.js routes and API proxy
│   ├── components/             # Triage and evaluation workspaces
│   └── lib/                    # SSE client and shared TypeScript types
└── docker-compose.yaml         # API, frontend, PostgreSQL, and DB initialization
```

## Running the project

### Requirements

The easiest path requires:

- Docker with Docker Compose; and
- an Anthropic API key and model name.

### Docker Compose

Create the backend environment file:

```bash
cp agent/.env.example agent/.env
```

Set at least these values in `agent/.env`:

```dotenv
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=your-anthropic-model
```

Then build and start the full application:

```bash
docker compose up --build
```

Open:

- Web application: [http://localhost:3000](http://localhost:3000)
- Evaluation workspace: [http://localhost:3000/evaluations](http://localhost:3000/evaluations)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

The Compose stack starts PostgreSQL, initializes and seeds the database, waits for the API health check, and then starts the frontend. The browser reaches the backend through the Next.js proxy, so a browser-facing CORS configuration is not required for this setup.

To stop the stack:

```bash
docker compose down
```

To also remove the local PostgreSQL volume and its seeded data:

```bash
docker compose down --volumes
```

### Run locally without Docker

For local development, install Python 3.13, [`uv`](https://docs.astral.sh/uv/), Node.js, `pnpm`, and PostgreSQL. Create `agent/.env` from the example and point `DATABASE_URL` to your local database.

Initialize and start the backend:

```bash
cd agent
uv sync
uv run python -m triage_ops.db.initialize
uv run fastapi dev
```

In another terminal, start the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend defaults to `http://127.0.0.1:8000`. Copy `frontend/.env.example` to `frontend/.env.local` if the API uses another address.

The backend also exposes a CLI after the database has been initialized:

```bash
cd agent
uv run triageops
```

## Tests and evaluations

Run the deterministic test suite:

```bash
cd agent
uv sync
uv run pytest
```

Run it with the branch-coverage gate:

```bash
uv run pytest \
  --cov=triage_ops \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml
```

Useful focused runs:

```bash
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not slow and not evaluation"
```

Model-backed evaluations are opt-in because they are slower, nondeterministic, and consume provider tokens. With the Anthropic environment variables configured, run the development corpus with:

```bash
cd agent
uv run python -m tests.evaluations.run_behavioral \
  --split development \
  --output behavioral-development.json
```

Run one development case with `--case-id dev-001`. The held-out split requires the additional `--confirm-held-out` flag and should be reserved for final regression measurement rather than prompt tuning.

## What I learned

The most important lesson from this project is that an agent is much more than a prompt plus a tool list. Most of the engineering work lives around the model.

### Keep authority in code

The model is useful for choosing evidence and synthesizing ambiguous information, but it should not decide whether an incident ID was valid, whether an approval payload matched pending work, or whether a side effect was authorized. Moving those decisions into deterministic code made the system easier to reason about and much easier to test.

### Design the state before the prompt

Graph state became the real contract of the application. Once authorization, pending approvals, final results, and decisions had explicit fields, node responsibilities and routing rules became clearer. Prompt changes alone could not provide the same guarantees.

### Tool errors are part of the agent protocol

The difficult path is not a successful lookup. It is distinguishing a retryable repository failure from a non-retryable error, preventing infinite loops, preserving safe error context, and still allowing the investigation to continue when supporting evidence is unavailable.

### Separate research from synthesis

Using one model loop to collect evidence and another constrained call to create the final report reduced the chance of mixing conversational text, incomplete conclusions, and executable proposals. It also created a clean place to validate the final incident identity and output schema.

### HITL is a state-machine problem

An approval button is not enough. Safe HITL requires stable proposal identities, an interrupt, durable pending state, strict decision validation, exactly-once execution semantics, and a public lifecycle the UI can display. The project implements the workflow shape, while some production guarantees still remain on the roadmap.

### Evaluations must inspect behavior, not just prose

Checking only the final answer misses whether the model queried future data, repeated the same tool, exceeded a log limit, or attempted an action before approval. Combining graph telemetry, deterministic checks, and a separate semantic judge produced a much more useful evaluation signal.

### Untrusted data stays untrusted

Operational data can contain instruction-like text. Moving it from a tool result into a different prompt does not make it safe. The trust boundary needs to remain explicit in tool descriptions, agent prompts, finalizer prompts, test fixtures, and output validation.

## Hardest parts

- **Balancing model autonomy and deterministic control.** The model needs enough freedom to investigate intelligently, while authorization, retries, query bounds, and mutations need hard application rules.
- **Designing interruption and resume.** Approval pauses one graph run and resumes another request against the same checkpointed thread without losing proposal state.
- **Normalizing streaming output.** LangGraph message chunks, state updates, interrupts, and custom events have different shapes. Converting them into one stable public SSE contract required careful ordering and validation.
- **Preventing loops without blocking legitimate retries.** Identical calls are tracked within the current user turn. A retry is allowed only after one retryable failure; successes and non-retryable failures cannot be repeated.
- **Building meaningful evaluations.** The corpus needs realistic failure modes and adversarial requests without leaking expected answers into the subject model's context.
- **Testing probabilistic architecture deterministically.** Scripted models, fake repositories, an in-memory checkpointer, and network blocking make graph behavior testable without provider calls.
- **Representing recommendations safely.** An action needs evidence-backed arguments, a discriminated schema, a human-readable rationale, and a separate trusted service mapping before it can even be considered for execution.

## Current limitations and tradeoffs

I want the README to be honest about what this project demonstrates and what it does not yet guarantee:

- The rollback, restart, feature-flag, and escalation services are simulations. They log the requested action, wait briefly, and return success; they do not change real infrastructure.
- Graph checkpoints are stored in memory. Conversations and interrupted approvals do not survive a process restart and cannot be safely shared across multiple API replicas.
- Threads are identified by UUID, but there is no user authentication, authorization, tenancy, or ownership check around a thread.
- The approval flow validates proposal IDs and decisions, but it does not yet verify the approving person's identity, role, or separation-of-duties policy.
- Execution does not yet have durable idempotency keys, distributed locks, reconciliation, cancellation, or crash recovery.
- The model layer currently supports Anthropic only, and there is no fallback, rate-limit policy, token budget, or cost control.
- Operational data comes from a small fictional dataset seeded into PostgreSQL. It does not model real data volume, retention, schema evolution, partial outages, or noisy telemetry.
- Evaluation code detects future-evidence use, but the repository interfaces do not enforce a scenario cutoff themselves. A stronger design would apply temporal access constraints below the model/tool layer.
- There is no full observability stack for traces, prompts, tool latency, token usage, costs, error rates, or evaluation drift.
- Prompt-injection defenses are layered instructions and deterministic boundaries, not a proof that arbitrary hostile content is harmless.
- The API and frontend need broader accessibility, load, browser, disconnect/reconnect, and end-to-end testing.

## Production-readiness roadmap

### Safety and identity

- [ ] Add authentication, thread ownership, tenant isolation, and role-based access control.
- [ ] Bind approvals to authenticated operators and enforce action-specific policies.
- [ ] Store an immutable audit trail for prompts, evidence, proposals, decisions, and execution results.
- [ ] Add secret detection/redaction, egress controls, and a formal prompt-injection threat model.
- [ ] Require server-side evidence references for every executable action argument.

### Durable agent execution

- [ ] Replace the in-memory checkpointer with a durable PostgreSQL-backed checkpointer.
- [ ] Add idempotency keys, execution leases, distributed locking, and recovery for interrupted actions.
- [ ] Define timeouts, cancellation, retry backoff, circuit breakers, and dead-letter handling.
- [ ] Handle multiple API replicas and concurrent requests against the same thread safely.
- [ ] Version graph state and support migrations for long-lived interrupted threads.

### Real integrations

- [ ] Replace simulated services with sandboxed adapters for deployment, flag, paging, and service-management platforms.
- [ ] Start with read-only or dry-run modes and narrowly scoped credentials.
- [ ] Add precondition checks and post-action verification rather than trusting a successful API response.
- [ ] Reconcile external state when an action succeeds remotely but the local process fails.

### Model operations

- [ ] Version prompts, schemas, models, and evaluation datasets together.
- [ ] Add model fallback policies, provider rate limiting, token budgets, and cost alerts.
- [ ] Capture model, node, and tool traces with privacy-aware retention.
- [ ] Run deterministic tests and development evaluations in CI; run held-out evaluations at controlled release gates.
- [ ] Monitor quality, safety, latency, cost, and tool-selection drift over time.

### Data and platform

- [ ] Add database migrations, backups, restore testing, connection-pool tuning, and retention policies.
- [ ] Enforce temporal evidence cutoffs and access policy in repository queries.
- [ ] Add pagination and scalable query paths for high-volume logs and metrics.
- [ ] Add API quotas, request-size limits, readiness checks, structured logging, metrics, and distributed tracing.
- [ ] Add deployment manifests, TLS, secret management, image scanning, and dependency/security update automation.

### Product quality

- [ ] Add full browser end-to-end tests for streaming, approvals, reset, failure, and reconnect paths.
- [ ] Improve accessibility and responsive behavior.
- [ ] Add saved investigations, searchable evidence, and auditable action history.
- [ ] Test the system with incident responders and revise the workflow based on real operational needs.

## Data and safety disclaimer

All organizations, users, services, incidents, logs, metrics, runbooks, credentials, and operational scenarios in this repository are fictional. Some records intentionally contain adversarial or misleading content for safety testing.

Do not connect this project to production infrastructure or grant it mutation credentials without implementing the missing identity, authorization, durability, observability, and execution-safety controls described above.

## Final note

This repository represents a learning milestone, not a finished destination. Building it taught me that AI engineering is the discipline of designing the system around the model: contracts, state, tools, safety boundaries, evaluations, failure handling, and user trust.

If you are reviewing this as a recruiter, engineer, or fellow learner, I hope the code makes those decisions visible and gives us something concrete to discuss.
