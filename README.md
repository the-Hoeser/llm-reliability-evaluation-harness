# LLM Reliability Evaluation Harness

A local-first research platform for measuring when language models answer, when they should abstain, and whether their stated confidence tracks answer correctness.

**Current milestone:** Sprint 2 — uncertainty and abstention research.

## Research question

Can a model recognize when the supplied evidence is insufficient, abstain instead of inventing an answer, and express confidence that tracks the correctness of answers it does provide?

The first benchmark measures **closed-context answerability**. It does not claim to determine whether a question is unknowable in the world. Every test case supplies a context and labels whether that context supports an answer, does not contain the answer, or is underspecified.

## Architecture

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, Pydantic, SQLAlchemy 2, Alembic
- **Execution:** sequential local Python worker
- **Database:** Neon PostgreSQL
- **Provider interface:** OpenAI-compatible Chat Completions API

```text
Research Workspace
    |
    v
FastAPI Controllers
    | datasets | models | experiments | runs
    |
    v
Local Execution Service
    |
    +--> Model Adapter --> OpenAI-compatible model
    |
    +--> Deterministic Evaluator
    |       | exact match
    |       + selective answering / confidence calibration
    |
    v
SQLAlchemy / Neon PostgreSQL
    |
    v
Raw Outputs + Decisions + Metrics + Execution Events
```

## Sprint 2 capabilities

1. Import versioned JSONL datasets through the API or dashboard.
2. Run a **forced-answer baseline** (`forced_answer_v1`) that asks the model to answer even when context is insufficient.
3. Run a **selective-answering condition** (`abstention_calibration_v1`) that allows an explicit abstention.
4. Request structured JSON output from OpenAI-compatible providers.
5. Persist raw response, confidence, abstention decision, latency, token usage, failure label, and detailed metrics.
6. Compare coverage, decision accuracy, answer accuracy, unknown abstention recall, false-answer rate, unnecessary abstention, Brier score, and 10-bin ECE.
7. Keep a dated research log with hypotheses, operational definitions, limitations, and literature notes.

## Benchmark labels

- `answerable`: the supplied context supports an answer. Gold output must include `acceptable_answers`, a non-empty list of strings.
- `unanswerable`: the requested information is absent from the supplied context.
- `underspecified`: the question/context does not identify a unique answer.

Unanswerable and underspecified cases are expected to trigger abstention in the selective-answering condition.

## Evaluation methods

| Method | Model instruction |
|---|---|
| `forced_answer_v1` | Always return the best proposed answer, even when context is insufficient. |
| `abstention_calibration_v1` | Answer only when supplied context supports it; otherwise return `answer: null` and `abstained: true`. |
| `normalized_exact_match` | Existing simple string exact-match evaluator. |

For both uncertainty methods, the JSON response includes an answer and a confidence value from 0 to 1. The selective condition also requires an `abstained` boolean.

**Confidence semantics:** the model's stated probability that its proposed answer is correct and supported by the supplied context. Abstentions have no proposed answer, so they are excluded from Brier and ECE denominators.

## Metrics

| Metric | Interpretation |
|---|---|
| Coverage | Valid responses that attempted an answer / all valid responses |
| Decision accuracy | Correct answer-versus-abstain actions / valid responses |
| Answer accuracy | Exact-match accuracy among attempted answerable cases |
| Unknown abstention recall | Correct abstentions / valid unanswerable and underspecified cases |
| False-answer rate | Answered cases / valid unanswerable and underspecified cases |
| Unnecessary-abstention rate | Abstentions / valid answerable cases |
| Brier score | Squared confidence error on attempted answers |
| ECE (10 bins) | Equal-width expected calibration error on attempted answers |

Small samples produce unstable calibration metrics. The included 12-case benchmark is a pipeline smoke test, not publication-grade evidence.

## Repository layout

- `frontend/` — research workspace UI
- `backend/app/api/routes/` — HTTP controllers
- `backend/app/services/model_adapter.py` — provider boundary and JSON mode
- `backend/app/services/evaluator.py` — normalized exact-match
- `backend/app/services/uncertainty.py` — structured abstention evaluation and calibration metrics
- `backend/app/services/execution.py` — local run orchestration
- `backend/app/db/` — SQLAlchemy models and sessions
- `backend/alembic/` — database migrations
- `datasets/abstention_context_v1.jsonl` — starter benchmark
- `research/RESEARCH_LOG.md` — dated research protocol and literature notes
- `docs/` — architecture and implementation plan

## Local setup

Requirements: Python 3.11+, Node.js 20+, npm.

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Copy `backend/.env.example` to `backend/.env`. Configure the Neon pooled URL for application traffic and the direct URL for migrations. Put the provider secret in the matching environment variable, for example `OPENAI_API_KEY`.

Run migrations and API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Liveness: http://127.0.0.1:8000/api/health
- Database readiness: http://127.0.0.1:8000/api/health/ready
- OpenAPI: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
# Copy .env.example to .env.local
npm run dev
```

Open http://localhost:3000. Import `datasets/abstention_context_v1.jsonl` in the Datasets panel, create a model configuration, then create two experiments against the same dataset and model: one forced-answer and one selective-answering.

## API flow

1. `POST /api/datasets/import-jsonl?name=...` — import a JSONL dataset as immutable version 1.
2. `POST /api/models` — register an OpenAI-compatible model. Only the credential environment-variable name is stored.
3. `POST /api/experiments` — select `forced_answer_v1` or `abstention_calibration_v1`.
4. `POST /api/experiments/{experiment_id}/runs` — execute locally.
5. `GET /api/runs/{run_id}` — retrieve the run summary and per-case outputs.

## Checks

```bash
# backend
cd backend
pytest
ruff check .

# frontend
cd frontend
npm run lint
npm run build
```

## Neon database

Project: `llm-reliability-lab` · Database: `reliability_lab` · PostgreSQL 17 · Region: `aws-us-east-2`.

Current Alembic revision after Sprint 2 migration: `0003_uncertainty_result_fields`. Credentials are intentionally not stored in Git.

## Research status

No live provider experiment has been run yet. The code includes fake-adapter tests for pipeline correctness. Research hypotheses and limitations are tracked in [research/RESEARCH_LOG.md](research/RESEARCH_LOG.md).
