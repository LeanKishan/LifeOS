# Architecture Decisions

Short records of *why* things are the way they are. Written so they can be
explained out loud in an interview. Newest at the bottom.

---

## ADR-0001 — Monorepo, separate frontend and backend

**Decision.** One git repo, two deployable apps: `backend/` (FastAPI) and
`frontend/` (Vite SPA), talking over HTTP/JSON.

**Why.** Keeps one history and one PR per feature that touches both sides, but
forces a real network boundary and an explicit API contract — the same contract
the future React Native app and the AI assistant will consume. A single
full-stack framework would blur that boundary.

**Trade-off.** Two dependency toolchains, CORS to configure, two dev servers.
Accepted for the API-design practice.

## ADR-0002 — FastAPI + synchronous SQLAlchemy 2.0

**Decision.** Sync `Session` in a thread-pool (FastAPI's default for sync deps),
not async SQLAlchemy, for now.

**Why.** Sync code is simpler to write correctly and to teach: no event-loop
foot-guns, straightforward tests, Alembic autogenerate works out of the box. At
the expected load (single user, later a handful) the thread-pool is nowhere near
a bottleneck.

**Revisit when.** A measured latency problem under concurrent load. Moving to
async then is a scoped change (engine, session, deps) and a good "before/after"
talking point.

## ADR-0003 — uv for Python dependency management

**Decision.** `uv` with `pyproject.toml` + `uv.lock`, dev deps in a PEP 735
dependency group.

**Why.** One fast tool for venv, resolution, locking, and running. Lockfile
gives reproducible installs locally, in CI, and in the Docker build. `pip install
uv` and no build back-end needed (`package = false`).

## ADR-0004 — PostgreSQL from day one, via Docker Compose

**Decision.** No SQLite phase. Postgres 16 in Compose, Alembic migrations from
the first model.

**Why.** SQLite hides real behaviour (types, constraints, concurrency, JSONB,
window functions used later in analytics). Compose makes "one command, whole
stack" true, which is also a target skill.

## ADR-0005 — JWT access + refresh tokens for auth

**Decision.** Short-lived access token (30 min) sent as `Authorization: Bearer`,
long-lived refresh token (14 d) used only to mint new access tokens. Refresh
rotation + a Redis revocation list land in M1/M8.

**Why.** Stateless request auth scales trivially and needs no session lookup on
the hot path; the refresh token limits the damage window of a leaked access
token. Argon2 (`pwdlib`) for password hashing — current OWASP recommendation.

**Trade-off.** Logout/ban needs the revocation list to be truly immediate;
without it, access tokens stay valid until they expire.

## ADR-0006 — Frontend: Vite + React + TS + Tailwind + Router + TanStack Query

**Decision.** Vite SPA, TanStack Query as the server-state layer, React Router
for routing, Tailwind for styling.

**Why.** TanStack Query removes most hand-rolled loading/error/caching state and
gives one obvious place for the API contract to live per feature. Vite keeps the
dev loop fast. Tailwind keeps styling in the component and avoids a growing pile
of CSS files.
