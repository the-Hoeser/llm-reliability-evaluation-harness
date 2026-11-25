# Architecture

## Selected shape

**Local-first modular monolith** with Neon PostgreSQL for persistent research records.

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Next.js, React, TypeScript, shadcn/ui | Research workspace |
| API | FastAPI | Validation, HTTP contracts, status codes |
| Brain | Python | Build immutable experiment plans |
| Harness | Python asyncio | Run lifecycle, bounded scheduling, cancellation |
| Sandbox | Local Python workers | Execute one test case at a time |
| Adapter | Provider-neutral interface | Translate provider requests and responses |
| Evaluator | Python | Deterministic metrics and optional validated judges |
| Analyzer | Python | Failure labels with evidence |
| Persistence | SQLAlchemy + Neon | Datasets, snapshots, outputs, scores, traces |

## Request ownership

- **Controller:** HTTP validation and response DTOs; no model calls or scoring.
- **Brain:** selects test cases and produces a reproducible plan.
- **Harness:** manages scheduling, concurrency, retries, cancellation, and run status.
- **Sandbox:** executes one bounded test task.
- **Model adapter:** translates provider-specific requests and responses.
- **Evaluator:** computes metrics without owning persistence.
- **Analyzer:** classifies outcomes without replacing raw outputs.
- **Repositories:** own database reads and writes.

## Vertical execution path

1. Controller validates an experiment run request.
2. Brain snapshots experiment, dataset, model, prompt, and evaluator settings.
3. Harness creates a run and schedules bounded test tasks.
4. A local worker invokes a provider adapter for one test case.
5. Evaluator calculates deterministic metrics where possible.
6. Analyzer assigns explicit failure labels and supporting evidence.
7. Repository persists output, scores, labels, usage, latency, and trace events.
8. Aggregator calculates run-level summaries.
9. Frontend reads run status and results.

## Reproducibility requirements

- Dataset versions are immutable once published; edits create a new version.
- Every run captures model and evaluator configuration snapshots.
- Store raw model outputs separately from scores and interpretations.
- Store judge model/configuration and its result independently from deterministic metrics.
- Keep a trace for each test case lifecycle.
- Make worker concurrency configurable and bounded.
- Treat retries as separate attempts or record attempt number; never silently overwrite earlier responses.

## First-release exclusions

No microservices, Kubernetes, cloud sandbox, distributed queue, multi-agent system, billing, or multi-tenant auth in Sprint 0. Local execution is deliberate; an execution interface will allow workers to move to cloud infrastructure later.
