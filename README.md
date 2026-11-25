# LLM Reliability Evaluation Harness

A research-oriented platform for discovering, measuring, and improving large language model reliability.

**Current milestone:** Sprint 1 — first end-to-end evaluation vertical slice.

## Architecture

A local-first modular monolith:

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, Pydantic, SQLAlchemy 2, Alembic
- **Execution:** sequential local Python worker (first slice)
- **Database:** Neon PostgreSQL
- **Provider interface:** OpenAI-compatible Chat Completions API

```text
Browser / Research Workspace
       |
       v
FastAPI Controllers
  | datasets | models | experiments | runs
       |
       v
Local Execution Service
       |
       +--> Model Adapter --> OpenAI-compatible provider
       |
       +--> Deterministic Evaluator
       |
       v
SQLAlchemy / Neon PostgreSQL
       |
       v
Run Details + Execution Events
```

## Current capabilities

1. Create a dataset with an immutable version 1 and stable test-case identifiers.
2. Store a SHA-256 checksum of the canonical test-case payload.
3. Register an OpenAI-compatible model endpoint.
4. Keep provider credentials in the backend process environment; only the environment-variable name is stored in the database.
5. Create an experiment linked to a dataset version and model configuration.
6. Execute up to 100 test cases sequentially on the local API process.
7. Persist raw model output, token usage when supplied, latency, deterministic scores, failure labels, and execution events.
8. Retrieve run summaries and per-case results through the API and dashboard.

## Research integrity notes

- The first evaluator is **normalized exact-match**. It lowercases and collapses whitespace; it does not remove punctuation or infer semantic equivalence.
- A mismatch is labelled `answer_mismatch`, not hallucination.
- Non-string expected outputs are marked unscored until a suitable evaluator is implemented.
- Model-based judges, confidence calibration, retries, background scheduling, and parallel workers are not implemented in this slice.
- The first local run is synchronous and sequential. Keep the API bound to localhost during development.

## Repository layout

- `frontend/` — research workspace UI
- `backend/app/api/routes/` — HTTP controllers
- `backend/app/services/model_adapter.py` — provider boundary
- `backend/app/services/evaluator.py` — deterministic scoring
- `backend/app/services/execution.py` — local run orchestration
- `backend/app/db/` — SQLAlchemy models and sessions
- `backend/alembic/` — database migrations
- `datasets/` — reviewed research datasets
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

Copy `backend/.env.example` to `backend/.env`. Use Neon's pooled URL for application traffic and the direct URL for migrations:

```env
DATABASE_URL=postgresql+psycopg://...-pooler.../reliability_lab?sslmode=require
DATABASE_URL_UNPOOLED=postgresql+psycopg://.../reliability_lab?sslmode=require
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=your-provider-key
```

Keep the key local. In the Model configuration form, use `OPENAI_API_KEY` as the credential environment variable name.

From `backend/`: `alembic upgrade head`, then `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.

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

Open http://localhost:3000.

## API flow

1. `POST /api/datasets` — create a dataset and first version.
2. `POST /api/models` — register an OpenAI-compatible model.
3. `POST /api/experiments` — bind the version and model.
4. `POST /api/experiments/{experiment_id}/runs` — execute locally.
5. `GET /api/runs/{run_id}` — retrieve run summary and results.

See the OpenAPI documentation at `/docs` for request and response schemas.

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

The initial eight domain tables plus the additive Sprint 1 columns are provisioned. Current Alembic revision: `0002_model_endpoint`. Credentials are intentionally not stored in Git.

See [docs/architecture.md](docs/architecture.md) and [docs/implementation-plan.md](docs/implementation-plan.md).
