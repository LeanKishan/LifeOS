# LifeOS

An all-in-one personal management platform — job tracker, learning tracker, finance,
calendar, project/Kanban boards, analytics, and an AI assistant that acts on your data
through the same API. One backend, one database, one auth system, shared infrastructure.

This repo is built **incrementally**. See [ROADMAP.md](ROADMAP.md) for the milestone plan
and [DECISIONS.md](DECISIONS.md) for why each piece is built the way it is.

**Built so far:** project foundation and CI · JWT authentication (register / login /
refresh, route guards) · **Job Tracker** — applications with a status pipeline,
companies, interviews, contacts, a board and table view, and search stats ·
**Kanban** — projects with custom columns, tasks with priorities / labels /
subtasks / comments, and a drag-and-drop board · **Calendar** — events with
iCalendar recurrence, reminders, and month / week views.

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
| Database        | SQLite (local dev) · PostgreSQL 16 (CI + prod) |
| Cache / queue   | Redis 7 (added in a later milestone)   |
| Background jobs | Celery (later milestone)               |
| Auth            | JWT access + refresh tokens            |
| Python tooling  | uv, Ruff, mypy, pytest                 |
| Containers      | Docker + Docker Compose                |
| CI              | GitHub Actions                         |

## Prerequisites

- Node 20+ and Python 3.12+ (the backend uses [uv](https://docs.astral.sh/uv/)).
- Docker is optional locally — see "Full stack with Postgres" below. CI and
  production always run against Postgres.

## Quickstart

```bash
# backend  ->  http://localhost:8000  (docs at /docs)
cd backend
uv sync
uv run uvicorn app.main:app --reload

# frontend ->  http://localhost:5173
cd frontend
npm install
npm run dev
```

With no `DATABASE_URL` set, the backend uses a local SQLite file
(`backend/lifeos.db`), so `/api/health` reports `database: ok` out of the box.

## Full stack with Postgres (needs Docker)

```bash
cp .env.example .env
docker compose up --build
```

Brings up Postgres, Redis, backend, and frontend together. This mirrors CI and
the deployment target. If Docker Desktop won't start (it needs hardware
virtualization / a working WSL2), the Quickstart path above is fully functional
without it.

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
