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

## ADR-0004 — PostgreSQL for CI and production; SQLite for local dev

**Decision.** Postgres 16 is the real database — it runs in Docker Compose, as a
service container in CI, and in production. Local development falls back to a
SQLite file when no `DATABASE_URL` is set. Alembic migrations run from the first
model, in batch mode so they apply on both engines.

**Why.** The original plan was Postgres everywhere via Compose. This machine
can't run Docker Desktop (no hardware virtualization / broken WSL2), and a native
Postgres install needs admin rights and manual role setup. Rather than block the
whole project on infrastructure, local dev uses SQLite — zero setup — while every
push still runs the full test suite and `alembic upgrade head` against a real
Postgres in GitHub Actions. CI, not the laptop, is the source of truth for DB
behaviour.

**Trade-off.** SQLite and Postgres diverge (types, constraints, concurrency, no
JSONB / arrays / window functions). Mitigations: keep models dialect-portable,
lean on CI to catch anything SQLite lets slide, and require Postgres from the
milestone where PG-specific features first appear (analytics). Flipping local dev
back to Postgres is one env var once Docker or a native install is available.

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

## ADR-0007 — Tokens in localStorage, transparent refresh on 401

**Decision.** The SPA keeps the access and refresh tokens in `localStorage`. An
axios request interceptor attaches the access token; a response interceptor
catches a 401, calls `/auth/refresh` once (concurrent 401s are coalesced onto one
refresh), retries the original request, and on failure clears the tokens and
drops to the login screen via a `lifeos:auth-cleared` window event.

**Why.** Simplest thing that works for a separate SPA and API with no shared
cookie domain, and it keeps the API purely stateless / CORS-simple.

**Trade-off.** `localStorage` is readable by any script, so an XSS bug leaks
tokens. What actually limits the blast radius: a short access-token lifetime
(30 min) now, and refresh-token rotation + a Redis revocation list in M8 so a
stolen refresh token can be killed. The httpOnly-cookie + CSRF-token design is
the fallback if requirements tighten.

## ADR-0008 — `OAuth2PasswordRequestForm` for login; email in the `username` field

**Decision.** `/auth/login` takes `application/x-www-form-urlencoded`
(`username`, `password`) via FastAPI's `OAuth2PasswordRequestForm`; `username`
carries the email. `register` and `refresh` stay JSON.

**Why.** Makes the Swagger UI "Authorize" button work with zero extra wiring and
matches the OAuth2 password-flow shape that the `OAuth2PasswordBearer` scheme
already documents. The frontend sends one `URLSearchParams` body for login and
JSON everywhere else.

## ADR-0009 — App refuses to start with a weak `JWT_SECRET` in production

**Decision.** `Settings.model_post_init` raises if `ENVIRONMENT=production` and
`JWT_SECRET` is missing, the dev placeholder, or shorter than 32 bytes.

**Why.** The single worst auth misconfiguration is shipping the default signing
key. Failing loudly at boot beats discovering it from forged tokens. In dev the
placeholder is fine and kept at 32+ bytes so HMAC-SHA256 doesn't warn.

## ADR-0010 — Feature modules: thin routes, logic in a service

**Decision.** Each domain gets one module per layer — `models/<x>.py`,
`schemas/<x>.py`, `services/<x>.py`, `api/routes/<x>.py`. Route handlers only
translate HTTP: auth, path params, and mapping a missing/again-not-owned row to
404 or a bad reference to 422. All querying and mutation lives in the service,
which never imports `fastapi`.

**Why.** Handlers stay readable at a glance. The service layer is callable from
the future AI-assistant tool layer (M10) and background jobs (M9) without going
through HTTP, and is unit-testable without a request. The `_*_or_404` helpers
keep per-user scoping in one obvious place per resource.

## ADR-0011 — Enums stored as their values, not member names

**Decision.**
`Enum(ApplicationStatus, native_enum=False, values_callable=lambda e: [m.value for m in e])`.

**Why.** SQLAlchemy's default persists the member *name* (`"APPLIED"`) and, on
Postgres, creates a native enum type that every change has to `ALTER TYPE`.
`native_enum=False` makes it a portable `VARCHAR + CHECK` on SQLite and Postgres
alike; `values_callable` makes the stored text match the API contract
(`"applied"`), so a raw query — or the AI assistant reading the table — sees the
same strings the API speaks. Adding a status is then an ordinary migration
(the CHECK is recreated in batch mode).

## ADR-0012 — Kanban ordering: dense integer positions, renumber on every move

**Decision.** Tasks (and columns, and subtasks) carry an integer `position` that
is always contiguous `0..n-1` within their parent. `POST /tasks/{id}/move` takes
`{column_id, position}`, pulls the task out, clamps the target index, re-inserts,
and renumbers the source and target columns. The frontend does the same move
against the cached board optimistically, then refetches.

**Why.** Trivial to reason about and to assert in tests, and "what order are the
cards in" has one obvious answer. At this scale a move rewrites a handful of
rows.

**Revisit when.** Boards get large or many people reorder the same board at once
— then a `move` touching every sibling row is contention. The standard fix is
fractional / lexicographic ranks (`0.5` between `0` and `1`, or a rank string) so
a move writes one row. Deferred until there's a reason.

## ADR-0013 — `user_id` denormalised onto every table

**Decision.** Every row in every feature module carries `user_id`, even when it
could be reached transitively (a subtask's owner is its task's owner is its
project's owner).

**Why.** Ownership checks stay a single `WHERE user_id = :me` on the table the
endpoint touches — no join back to the root for a 404 decision, and one obvious
place per resource (`_*_or_404`). The cost is keeping `user_id` correct on
insert, which the service layer does in one spot.
