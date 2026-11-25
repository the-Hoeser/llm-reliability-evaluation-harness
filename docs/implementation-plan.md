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

## Sprint 1 — First end-to-end evaluation slice

- [x] Dataset creation with immutable version 1 and checksum
- [x] OpenAI-compatible model configuration
- [x] Experiment creation with dataset/model references
- [x] Local sequential execution service
- [x] Normalized exact-match evaluator
- [x] Per-case result and execution-event persistence
- [x] Dashboard for dataset/model/experiment creation and local runs
- [x] CI tests, lint, and production build passing

## Sprint 2 — Uncertainty and abstention research

- [x] Define closed-context answerability labels: answerable, unanswerable, underspecified
- [x] Add JSONL dataset import
- [x] Add forced-answer baseline evaluator mode
- [x] Add abstention-enabled evaluator mode
- [x] Add JSON-mode support to the OpenAI-compatible adapter
- [x] Persist confidence and abstention as first-class result fields
- [x] Measure coverage, decision accuracy, false-answer rate, abstention recall, unnecessary abstention, Brier score, and ECE
- [x] Add a small context-grounded smoke benchmark
- [x] Maintain a dated research log and literature notes
- [ ] Verify Sprint 2 backend tests and frontend production build in CI
- [ ] Run the first live provider experiment with a locally configured API key
- [ ] Compare paired forced-answer and abstention-enabled runs
- [ ] Expand and manually review the benchmark before making research claims

**Acceptance criterion:** run both policies on the same dataset/model configuration, persist raw outputs and metrics, and inspect the measured answer/abstain trade-off.

## Research integrity requirements

- The current benchmark measures answerability relative to a supplied context, not global knowledge.
- Self-reported confidence is a measurement signal, not ground truth about a model's internal state.
- Confidence calibration is calculated only for attempted answers.
- Invalid structured responses and provider errors remain visible in totals and are excluded from valid-response denominators.
- A small smoke benchmark is useful for pipeline verification, not publication-grade evidence.

## Later milestones

- Repeated trials, randomized condition order, uncertainty intervals, and model-version tracking.
- Larger human-reviewed benchmark sets and domain-stratified analysis.
- Semantic answer evaluation with validated references or independent human review.
- Risk-coverage curves and cost-sensitive abstention thresholds.
- Retrieval/context quality experiments and controlled interventions.
- Multi-model comparisons and failure-taxonomy expansion.
