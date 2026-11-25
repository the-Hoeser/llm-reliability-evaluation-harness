# Implementation plan

## Sprint 0 — Foundation

- [x] Monorepo and repository conventions
- [x] FastAPI application entry point
- [x] Liveness and database-readiness routes
- [x] SQLAlchemy base and initial domain models
- [x] Alembic configuration and initial migration
- [x] Next.js light-theme workspace shell
- [x] Environment examples and setup documentation
- [x] Neon project provisioned and initial schema applied
- [ ] Verify the frontend production build on the developer machine

## Sprint 1 — First end-to-end vertical slice

- [x] Dataset creation with immutable version 1 and checksum
- [x] Test-case validation and duplicate ID rejection
- [x] OpenAI-compatible model configuration (secrets stay in environment variables)
- [x] Experiment creation with dataset/model references and system-prompt snapshot
- [x] Local sequential execution service with a 100-case cap
- [x] Normalized exact-match evaluator for string ground truth
- [x] Per-case result and execution-event persistence
- [x] Run summary and run-detail endpoints
- [x] Workspace UI forms for dataset, model, experiment, and local run
- [ ] Verify all tests and frontend build in a clean local environment
- [ ] Verify a real provider call using the user's configured API key

**Acceptance criterion:** create a dataset, configure a model, create an experiment, execute it, and inspect persisted outputs, scores, and traces.

## Research and correctness notes

- Exact-match is a narrow metric, not a general measure of factuality or reasoning.
- Cases with non-string expected outputs remain unscored until an evaluator is explicitly implemented.
- A score of 0 means the normalized strings differ; it does not by itself prove hallucination.
- Model-based judges are not included in this slice.
- Runs execute synchronously and sequentially in the local FastAPI process. Durable background scheduling, cancellation, and bounded parallelism are later milestones.

## Later research milestones

- JSONL dataset import and immutable additional dataset versions.
- Bounded concurrent local workers, cancellation, timeouts, and explicit retry attempts.
- Failure taxonomy and human-review workflow.
- Multi-model comparisons and controlled interventions.
- Confidence calibration and selective prediction.
- Cloud worker execution only after the local execution interface is stable.
