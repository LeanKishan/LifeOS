# LifeOS

An all-in-one personal management platform — job tracker, learning tracker, finance,
calendar, project/Kanban boards, analytics, and an AI assistant that acts on your data
through the same API. One backend, one database, one auth system, shared infrastructure.

This repo is built **incrementally**. See [ROADMAP.md](ROADMAP.md) for the milestone plan
and [DECISIONS.md](DECISIONS.md) for why each piece is built the way it is.

## Architecture

```
                 React + Vite (SPA)
                        |
                     HTTP / JSON
                        |
                 FastAPI (Python)
        ________________|________________
       |         |            |          |
   PostgreSQL   Redis      WebSockets   AI service
       |         |
       |      Celery workers
```

## Stack

| Area            | Choice                                  |
| --------------- | --------------------------------------- |
| Frontend        | React 19 + TypeScript + Vite            |
| Styling         | Tailwind CSS                            |
| Server state    | TanStack Query                          |
| Routing         | React Router                            |
| Backend         | FastAPI (Python 3.12)                   |
| ORM / migrations| SQLAlchemy 2.0 + Alembic               |
| Database        | PostgreSQL 16                           |
| Cache / queue   | Redis 7 (added in a later milestone)   |
| Background jobs | Celery (later milestone)               |
| Auth            | JWT access + refresh tokens            |
| Python tooling  | uv, Ruff, mypy, pytest                 |
| Containers      | Docker + Docker Compose                |
| CI              | GitHub Actions                         |

## Prerequisites

- **Docker Desktop** — install: `winget install -e --id Docker.DockerDesktop`, then reboot.
- Node 20+ and Python 3.12+ only needed if you want to run a service outside Docker.

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health:   http://localhost:8000/api/health

## Running a service directly (no Docker)

```bash
# backend
cd backend
uv sync
uv run uvicorn app.main:app --reload      # http://localhost:8000

# frontend
cd frontend
npm install
npm run dev                               # http://localhost:5173
```

Without a database running, `/api/health` reports `database: unavailable` but the API
still serves — bring up Postgres (`docker compose up db`) for full function.

## Repo layout

```
backend/
  app/
    core/        config, DB engine, security (hashing + JWT)
    models/      SQLAlchemy models (one module per domain)
    schemas/     Pydantic request/response models
    api/routes/  one router per feature module
    migrations/  Alembic
  tests/
frontend/
  src/
    lib/         API client, query client
    features/    one folder per feature module
    pages/       route-level screens
    components/   shared UI
infra/           Compose/monitoring extras (grows later)
```

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck && npm run build
```
