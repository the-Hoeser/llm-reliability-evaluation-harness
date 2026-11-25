# Architecture

## Selected shape

**Local-first modular monolith** with Neon PostgreSQL for persistent research records.

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Next.js, React, TypeScript, shadcn/ui | Research workspace |
| API | FastAPI | Validation, HTTP contracts, status codes |
| Brain | Python | Build immutable experiment plans |
| Harness | Python | Run lifecycle, scheduling and cancellation |
| Sandbox | Local Python worker | Execute one test case at a time |
| Adapter | Provider-neutral interface | Translate provider requests and responses |
| Evaluator | Python | Deterministic metrics and optional validated judges |
| Analyzer | Python | Failure labels with supporting evidence |
| Persistence | SQLAlchemy + Neon | Datasets, snapshots, outputs, scores and traces |

## Current vertical slice

1. Controller validates dataset, model, and experiment requests.
2. Dataset creation stores a dataset, immutable version 1, test cases, and a SHA-256 checksum.
3. Experiment creation references one dataset version and one model configuration.
4. The run service snapshots model, evaluator, and system-prompt configuration.
5. A local sequential worker calls the OpenAI-compatible Chat Completions API.
6. The evaluator applies normalized exact-match only when the expected output is a string.
7. Each output and score is persisted in `test_results`; lifecycle events are persisted in `execution_events`.
8. The run summary records scored/unscored counts, mean score, errors, and failure categories.
9. The UI retrieves the run and displays its saved results.

## Request ownership

- **Controller:** HTTP validation and response DTOs; no direct model calls or scoring.
- **Brain:** future home of experiment-plan generation.
- **Harness:** currently a local sequential execution service; bounded parallelism and cancellation are future work.
- **Sandbox:** a single test-case execution boundary; currently runs in the API process.
- **Model adapter:** provider-specific request and response translation.
- **Evaluator:** computes metrics without owning persistence.
- **Analyzer:** future expansion of evidence-based failure classification.
- **Repositories/services:** database access and orchestration logic.

## Reproducibility requirements

- Dataset versions are immutable; edits create a new version.
- Every run captures model and evaluator configuration snapshots.
- System prompt is snapshotted at run start.
- Store raw model outputs separately from scores and interpretations.
- Store judge model/configuration and its result separately from deterministic metrics.
- Keep a trace event for each test case lifecycle.
- Make worker concurrency configurable when parallelism is introduced.
- Treat retries as separate attempts or record attempt number; never silently overwrite earlier responses.

## Metric limitations

Normalized exact-match lowercases text and compresses whitespace; it does not remove punctuation, establish semantic equivalence, or prove factuality. Non-string expected-output formats are explicitly marked unscored. A mismatch is labeled `answer_mismatch`, not hallucination.

## First-release exclusions

No microservices, Kubernetes, cloud sandbox, distributed queue, multi-agent system, billing, or multi-tenant auth. The API is intended to be run on localhost during this development stage; it does not yet have user authentication.
