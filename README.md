# LLM Reliability Evaluation Harness

A research-oriented platform for discovering, measuring, and improving large language model reliability.

**Current milestone:** Sprint 0 — local-first repository and service foundation.

## Architecture

A modular monolith: Next.js research workspace → FastAPI controller → experiment planner → bounded harness → local test worker → provider adapter → evaluator and failure analyzer → Neon PostgreSQL.

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic
- **Execution:** local Python workers, introduced after the foundation
- **Database:** Neon PostgreSQL

The first end-to-end slice will run one versioned dataset against one configured model, persist raw outputs and execution metadata, calculate deterministic scores where ground truth permits, and display the results.

## Principles

1. Preserve dataset, model, prompt, and evaluator configuration snapshots for reproducibility.
2. Store raw inputs and outputs separately from scores and interpretations.
3. Prefer deterministic metrics when appropriate; validate model-based judges.
4. Keep worker concurrency bounded and retries explicit.
5. Never commit provider keys or database URLs.

## Repository layout

- `frontend/` — research workspace UI
- `backend/app/api/` — HTTP controllers
- `backend/app/brain/` — experiment planning (next milestone)
- `backend/app/harness/` — scheduling and lifecycle (next milestone)
- `backend/app/sandbox/` — local workers (next milestone)
- `backend/app/evaluator/` — metrics (next milestone)
- `backend/app/analyzer/` — failure classification (next milestone)
- `backend/app/db/` — SQLAlchemy models and sessions
- `backend/alembic/` — database migrations
- `datasets/` — reviewed research datasets
- `docs/` — architecture and implementation notes

## Local setup

Requirements: Python 3.11+, Node.js 20+, npm.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

Copy `backend/.env.example` to `backend/.env`. Use Neon's pooled URL for application traffic and the direct URL for migrations:

```env
DATABASE_URL=postgresql+psycopg://...-pooler.../reliability_lab?sslmode=require
DATABASE_URL_UNPOOLED=postgresql+psycopg://.../reliability_lab?sslmode=require
CORS_ORIGINS=http://localhost:3000
```

From `backend/`, run `alembic upgrade head`, then `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.

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

## Checks

```bash
# backend
cd backend && pytest && ruff check .
# frontend
cd frontend && npm run lint && npm run build
```

## Neon database

Project: `llm-reliability-lab` · Database: `reliability_lab` · PostgreSQL 17 · Region: `aws-us-east-2`.

The initial eight domain tables and Alembic revision `0001_initial_schema` have been provisioned and verified. Credentials are intentionally not stored in Git.

## Status

- [x] Neon project provisioned and connectivity verified
- [x] Initial database schema applied
- [x] FastAPI app and health/readiness routes scaffolded
- [x] SQLAlchemy models and Alembic migration added
- [x] Next.js light-theme workspace shell scaffolded
- [ ] Verify local API → Neon readiness
- [ ] Wire the UI to real API data
- [ ] Build the first end-to-end evaluation flow

See [docs/architecture.md](docs/architecture.md) and [docs/implementation-plan.md](docs/implementation-plan.md).
