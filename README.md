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
iCalendar recurrence, reminders, and month / week views · **Finance** — accounts,
categorised transactions (integer cents), monthly budgets, CSV import, and a
budget-vs-actual summary · **Learning** — courses with lessons and progress,
plus SM-2 spaced-repetition flashcards · **Real-time** — a WebSocket push channel
so a change on one device refreshes the others · **Redis** — immediate token
revocation, auth rate limiting, and a cached dashboard summary · **Background
jobs** — Celery tasks for due-reminder notifications, a daily digest, and a
monthly finance PDF · **AI assistant** — a tool-using chat that reads your data
and can add tasks, events, and flashcards · **Analytics** — cross-module
productivity / finance / learning aggregates with CSV & PDF export ·
**Security pass** — security headers, body-size and write-rate limits, a generic
error boundary, a production config guard, and dependency scanning in CI
(see [SECURITY.md](SECURITY.md)) · **Deployment** — multi-stage images and a
Terraform stack (`infra/`) that puts the app on AWS ECS Fargate behind an ALB
with RDS, ElastiCache, S3 and a GitHub-OIDC release pipeline
(see [infra/README.md](infra/README.md)) · **Monitoring** — structured JSON
logs, per-request IDs, Prometheus metrics with a Grafana dashboard, optional
Sentry, a readiness probe, and a Redis pub/sub WebSocket fan-out so live updates
survive multiple API instances · **Mobile** — an Expo (React Native) app in
`mobile/` sharing the API contract: auth, a dashboard, and the job tracker
(see [mobile/README.md](mobile/README.md)).

## Architecture

```
        React + Vite (SPA)   Expo (React Native)
                   \             /
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
| Mobile          | Expo (React Native) + expo-router      |
| Styling         | Tailwind CSS                            |
| Server state    | TanStack Query                          |
| Routing         | React Router                            |
| Backend         | FastAPI (Python 3.12)                   |
| ORM / migrations| SQLAlchemy 2.0 + Alembic               |
| Database        | SQLite (local dev) · PostgreSQL 16 (CI + prod) |
| Cache / revocation | Redis 7 · fakeredis for local dev   |
| Background jobs | Celery · eager in dev, worker + beat in Compose |
| AI              | Anthropic SDK (`claude-opus-5`), manual tool-use loop |
| Auth            | JWT access + refresh tokens            |
| Python tooling  | uv, Ruff, mypy, pytest                 |
| Containers      | Docker (multi-stage) + Docker Compose  |
| Infra           | AWS ECS Fargate · ALB · RDS · ElastiCache · S3 · Terraform |
| Observability   | JSON logs · Prometheus `/metrics` · Grafana · Sentry · CloudWatch alarms |
| CI / CD         | GitHub Actions · OIDC · Trivy image scan |

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

For a production-parity run — the same multi-stage `prod` images, a one-off
migration task, and a `gateway` that path-routes like the ALB:

```bash
JWT_SECRET=$(openssl rand -hex 32) docker compose -f docker-compose.prod.yml up --build
# app on http://localhost:8080
```

## Deploying to AWS

`infra/` is a Terraform stack that runs the app on ECS Fargate behind an ALB,
with RDS Postgres, ElastiCache Redis, an S3 bucket, ECR, autoscaling, and a
GitHub-OIDC release pipeline (`.github/workflows/release.yml`) that builds,
scans, migrates, and rolls the services. See [infra/README.md](infra/README.md)
for the bootstrap-and-apply steps and [DECISIONS.md](DECISIONS.md) ADR-0023 for
the topology rationale.

## Observability

The API logs one structured line per request (`LOG_JSON=true` in the prod image),
tags every request with an `X-Request-ID`, and exposes Prometheus metrics at
`/metrics`. For a local view:

```bash
JWT_SECRET=$(openssl rand -hex 32) \
  docker compose -f docker-compose.prod.yml -f docker-compose.observability.yml up --build
# Grafana http://localhost:3001 (anon viewer) · Prometheus http://localhost:9090
```

Set `SENTRY_DSN` to turn on error tracking. `GET /api/health/ready` is the
readiness probe (checks Postgres + Redis). ADR-0024 has the rationale.

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
  docker/        prod entrypoint (serve / migrate / worker / beat)
frontend/
  src/
    lib/         API client, query client
    features/    one folder per feature module
    pages/       route-level screens
    components/   shared UI
  docker/        nginx.conf for the static prod image
mobile/          Expo (React Native) app — auth + dashboard + job tracker
  app/           expo-router file routes
  src/           api client, auth, feature hooks, UI
infra/
  *.tf           Terraform — ECS Fargate stack
  bootstrap/     one-off remote-state bucket + lock table
  observability/ Prometheus scrape config + Grafana provisioning
  compose/       gateway config for docker-compose.prod.yml
```

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck && npm run build
```
