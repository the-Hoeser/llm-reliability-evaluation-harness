# Implementation plan

## Sprint 0 — Foundation

- [x] Monorepo and repository conventions
- [x] FastAPI application entry point
- [x] Liveness and database-readiness routes
- [x] SQLAlchemy base and initial domain models
- [x] Alembic configuration and initial migration
- [x] Next.js light-theme workspace shell
- [x] Environment examples and setup documentation
- [ ] Install dependencies and verify local runtime
- [ ] Configure local Neon credentials
- [ ] Verify local API → Neon readiness

## Sprint 1 — First end-to-end vertical slice

1. Add dataset and dataset-version CRUD.
2. Import a small, manually reviewed JSONL dataset.
3. Define a provider-neutral model adapter protocol.
4. Implement one provider adapter; keys remain in environment variables.
5. Execute one test case through one local worker.
6. Persist raw response, latency, token usage (when supplied), and execution events.
7. Add a deterministic evaluator for a narrow task with verifiable expected answers.
8. Display one real run and its results in the UI.

**Acceptance criterion:** a user can create an experiment, execute a dataset against a configured model, and inspect persisted results and traces.

## Later research milestones

- Bounded concurrent local workers, cancellation, timeout, and retry handling.
- Failure taxonomy and human-review workflow.
- Multi-model comparisons and controlled interventions.
- Confidence calibration and selective prediction.
- Cloud worker execution only after the local interface is stable.

## Definition of done for Sprint 0

- Backend imports and exposes health routes.
- Alembic can connect with the direct Neon URL.
- Readiness endpoint executes `SELECT 1` using the pooled Neon URL.
- Frontend builds and renders without fabricated benchmark metrics.
