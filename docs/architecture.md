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
| Evaluator | Python | Deterministic metrics, structured abstention evaluation |
| Analyzer | Python | Failure labels with supporting evidence |
| Persistence | SQLAlchemy + Neon | Datasets, snapshots, outputs, scores and traces |

## Sprint 2 research slice

The research question is: **Can a model recognize when supplied evidence is insufficient, abstain instead of inventing an answer, and calibrate its confidence on answers it does provide?**

The first benchmark is closed-context. Each case contains a question, context, and an expected-output object with one of three labels: `answerable`, `unanswerable`, or `underspecified`.

Two evaluator modes are available:

- `forced_answer_v1`: baseline condition. The model must produce an answer and a confidence probability, even when evidence is missing.
- `abstention_calibration_v1`: selective condition. The model may return `answer: null` and `abstained: true` when evidence is missing or ambiguous.

Both modes request JSON output. The effective system prompt is snapshotted on the evaluation run. Model confidence means the probability that a proposed answer is correct and supported by the supplied context.

## Sprint 2 metrics

- **Coverage:** fraction of valid responses that attempted an answer.
- **Decision accuracy:** correct answer-versus-abstain actions among valid responses.
- **Answer accuracy on attempted answerable:** exact-match accuracy on answerable cases where an answer was attempted.
- **Unknown abstention recall:** fraction of valid unanswerable and underspecified cases correctly abstained.
- **False-answer rate on unknown:** fraction of valid unanswerable and underspecified cases answered anyway.
- **Unnecessary-abstention rate:** fraction of valid answerable cases the model unnecessarily abstained on.
- **Brier score:** mean squared error of stated confidence against correctness on attempted answers.
- **ECE:** 10-bin equal-width expected calibration error on attempted answers.

Abstentions are excluded from confidence calibration because they have no proposed answer. Provider errors and invalid JSON are tracked separately and excluded from valid-response denominators.

## Request ownership

- **Controller:** HTTP validation and response DTOs; no direct model calls or scoring.
- **Brain:** future home of experiment-plan generation.
- **Harness:** local sequential execution and run lifecycle.
- **Sandbox:** a single test-case execution boundary; currently runs in the API process.
- **Model adapter:** provider-specific request/response translation; can request JSON mode for structured evaluator protocols.
- **Evaluator:** deterministic exact-match and uncertainty metrics without owning persistence.
- **Analyzer:** future expansion of evidence-based failure classification.
- **Repositories/services:** database access and orchestration logic.

## Reproducibility requirements

- Dataset versions are immutable; edits create a new version.
- Every run captures model and evaluator configuration snapshots.
- The effective system prompt is snapshotted at run start.
- Store raw model outputs separately from scores and interpretations.
- Store confidence and abstention as first-class result fields, with detailed metrics in JSON.
- Keep a trace event for each test case lifecycle.
- Repeat experimental conditions and report variation before drawing conclusions.
- Treat provider/model version changes as separate experimental configurations.

## Metric limitations

- Confidence is verbalized self-report, not an internal probability read from model logits.
- Exact-match is narrow and may penalize valid paraphrases.
- The current benchmark is short, synthetic, and closed-context; it is a pipeline smoke benchmark, not a representative evaluation suite.
- Calibration estimates from small samples are unstable.
- Closed-context unanswerability is not equivalent to global lack of knowledge.

## First-release exclusions

No microservices, Kubernetes, cloud sandbox, distributed queue, multi-agent system, billing, or multi-tenant auth. The API is intended to be run on localhost during development; it does not yet have user authentication.
