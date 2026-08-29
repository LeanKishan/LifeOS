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

## ADR-0014 — Datetimes are naive UTC; recurrence is an RRULE string

**Decision.** Every stored datetime is naive and understood as UTC. The API
accepts an ISO value with an offset, converts to UTC, and drops the tzinfo on the
way in; on the way out a serializer re-attaches `+00:00`. Recurring events store
one iCalendar RRULE string (`FREQ=WEEKLY;BYDAY=MO;COUNT=10`), not a rules table.
`GET /calendar/occurrences?from=&to=` expands events into instances with
`dateutil.rrule`, capped at 400 days / 750 instances.

**Why.** Naive-UTC storage sidesteps SQLite's lack of real `timestamptz` and
keeps SQLite and Postgres behaving identically; UTC-everywhere means comparisons
and arithmetic never surprise. RRULE is the interchange format calendars already
speak, so a client library produces it directly and there's nothing bespoke to
reimplement. The rrule maths runs tz-aware internally so an `UNTIL=...Z` in the
rule validates.

**Not done.** Per-instance overrides (move/rename/cancel one occurrence, i.e.
`RECURRENCE-ID` + `EXDATE`) and non-UTC display rules — both land when the
calendar UI needs them.

## ADR-0015 — Money is integer cents; enforce SQLite foreign keys

**Decision.** Every monetary amount is a non-negative integer number of cents,
paired with a `TransactionKind` (`income` / `expense`) — never a float, never a
signed amount. Balances and rollups are `SUM`s in the database, split by kind.
Separately, the engine turns on `PRAGMA foreign_keys=ON` for every SQLite
connection.

**Why.** Floats can't represent `0.10` exactly, so they drift under addition;
integer cents are exact and `SUM`s stay exact. A `kind` column (rather than
sign) keeps "how much did I spend on groceries" a plain `WHERE kind='expense'`
without `ABS`/`CASE`. SQLite ignores `ON DELETE CASCADE` / `SET NULL` unless
asked per connection — turning it on makes local dev enforce the same referential
actions that Postgres already does in CI and production, so the cascade tests
mean something on both.

## ADR-0016 — Flashcard scheduling is SM-2, as a pure function

**Decision.** `learning.apply_sm2(card, quality, today)` mutates a card's
`ease_factor`, `interval_days`, `repetitions`, and `due_on` in place, using the
standard SuperMemo-2 formulas. `today` is a parameter, not `date.today()`. The
review endpoint calls it with the real date; the tests call the function
directly with a fixed date.

**Why.** Spaced-repetition scheduling is the one piece of real algorithmic
behaviour in this module and it has fiddly edge cases (first three reps are
special-cased, ease has a 1.3 floor, a lapse resets the streak). Keeping it a
pure `(card, quality, today) -> None` makes every case a two-line unit test with
no database or HTTP. SM-2 itself is chosen because it's well documented and
"good enough" — swapping in FSRS later is a change to this one function.

## ADR-0017 — Live updates: coarse "channel changed" events, emitted by middleware

**Decision.** The WebSocket carries `{"type": "<channel>"}` frames, where
`<channel>` is the top-level TanStack Query key for a feature (`projects`,
`job-tracker`, `calendar`, ...). The client's only reaction is
`invalidateQueries({ queryKey: [type] })`. One `http` middleware emits the frame
to the acting user after any 2xx `POST/PUT/PATCH/DELETE` under that feature's
path prefix — routes and services know nothing about it.

**Why.** "Something in projects changed, refetch what you're showing" is enough
for a single-user-multi-device app and costs one middleware instead of a
`publish()` call in ~40 handlers. TanStack Query already de-dupes and only
refetches queries that are actually mounted. Fine-grained events (which task,
which field) and an actor id to skip the originating tab are a later refinement
if payloads get expensive.

**Not done.** The `ConnectionManager` is per-process — a second web worker
wouldn't see the first's connections. Multi-worker needs the emit to go through
Redis pub/sub with every worker subscribed. `publish()` now mirrors each event
onto a Redis channel as that seam, but nothing consumes it in-repo (fakeredis's
pub/sub consumer hangs, and a real subscriber process belongs with the deploy in
M13). Single-worker delivery is the direct in-process call.

## ADR-0018 — Redis: a fakeredis dev fallback; revocation, rate limits, cache

**Decision.** `REDIS_URL=fakeredis://` (the dev default) gets an in-process
`fakeredis` server; any other URL is a real client. CI and prod run real Redis.
Redis then backs three things:

- **Token revocation.** Tokens carry a `jti` and a `gen`. `/auth/logout` denylists
  the presented access + refresh `jti` (key TTL = the token's remaining life);
  `/auth/logout-all` bumps a per-user `gen` counter and every check rejects tokens
  minted under an older `gen`. `get_current_user` consults both, so logout is now
  immediate rather than "valid until it expires" (the M1 gap).
- **Rate limiting.** A fixed-window per-IP counter as a FastAPI dependency —
  10/min on login, 5/min on register, `429` + `Retry-After`.
- **Response cache.** `/finance/summary` and `/job-tracker/stats` store their JSON
  under `cache:<channel>:<user>:v<version>:<params>` for 30 s; the M7 mutation
  middleware `INCR`s the version, so the next read misses and recomputes. No
  `SCAN`/`DEL` — stale keys age out on their own TTL.

**Why fakeredis.** Same reason as SQLite for the DB: local dev shouldn't need a
service running. The code path is identical (`redis-py` API); only the client
construction differs. The `gen` counter (rather than a "tokens valid after"
timestamp) exists because JWT `iat` is whole-second — a token minted in the same
second as a "sign out everywhere" would otherwise slip through.

## ADR-0019 — Celery: eager in dev, a real worker in Compose

**Decision.** `CELERY_EAGER=true` (the dev/test default) makes `.delay()` run the
task synchronously in the caller with exceptions propagated — no broker, no
worker. Compose sets it `false` and runs `worker` + `beat` services against a
Redis broker. Tasks open their own DB session via `app.core.db.SessionLocal`
(they're outside a request); the test fixture repoints that name at the
in-memory engine so an eager task sees the request's data.

**Why.** A background job is only "background" in production; for a single
developer, running it inline is indistinguishable and needs nothing installed.
The task *code* is identical either way, so the eager path still exercises it.
Tasks that must be async in prod (a slow PDF render, fan-out over every user)
are written as tasks now; flipping the flag is the only change to make them
actually asynchronous.

**Notifications.** `dispatch_due_reminders` is the first producer of
`{"type": "notification"}` WS frames — the source M7's toast tray was waiting
for. At-most-once delivery is a Redis `SET key NX EX` per (reminder, occurrence),
not a DB column, because it's ephemeral and self-expiring.

## ADR-0020 — AI assistant: a manual loop, tools *are* the service layer

**Decision.** `/api/coach/chat` runs a hand-written
`while stop_reason == "tool_use"` loop against `claude-opus-5` (adaptive
thinking, `effort=medium`, capped at 6 iterations). The six tools call the same
`app.services.*` functions the HTTP routes call — not the routes — so there's no
loopback request, and every call is passed the request's `db` session and
`user_id`. `execute_tool` catches `LookupError`/`ValueError`/`KeyError` and
returns `"error: ..."` as the tool result instead of raising, so the model
recovers from a bad project name or malformed date on its own. The endpoint is
stateless: the client resends the whole message history, mirroring the Messages
API itself.

**Why a manual loop over the SDK Tool Runner.** The loop is ~15 lines, it's the
thing to be able to explain in an interview, and it needs no beta surface. The
Tool Runner would save the boilerplate but hides exactly the part worth
understanding.

**Why tools = services.** ADR-0010 kept all logic out of the routes for this
moment: the assistant, Celery tasks (M9), and a future mobile client all reach
the same code without going through FastAPI. `create_task` reusing
`projects_svc.create_task` means the assistant can't drift from the app's rules.

**Config.** `ANTHROPIC_API_KEY` empty → the endpoint 503s and nothing else is
affected; the key is passed explicitly to `Anthropic(api_key=...)` rather than
relying on ambient credentials. Tests mock the client entirely — no key, no
network.

## ADR-0021 — Analytics: the DB groups the cardinal dimensions, the app buckets time

**Decision.** `/analytics/overview` runs real `GROUP BY` in SQL for the
low-cardinality splits — open tasks by priority, applications by status, expense
by category (`SUM` + `ORDER BY` + `LIMIT`). The time series (tasks done per week,
lessons per week, net per month, applications per week) are computed in Python by
fetching the relevant `(date, value)` rows for the requested range and bucketing
them by ISO-week Monday (or `YYYY-MM`).

**Why.** SQLite has no `date_trunc`; `strftime` vs `to_char` would mean a dialect
branch in every series query. The range filter bounds the fetch to at most ~a
year of rows per module, so bucketing in the service is cheap and reads
identically on SQLite and Postgres. The genuinely set-shaped aggregations stay
in SQL where they belong.

**Task completion.** M3 modelled a task's state purely as which column it's in —
no timestamp, so "throughput" and "cycle time" weren't derivable. M11 adds
`Task.done` + `Task.completed_at` (stamped on the transition) as the minimal
change that makes productivity analytics real, rather than inferring "done" from
a column name.

## ADR-0022 — Security pass: headers + limits as middleware, a hard prod-config guard

**Decision.** Four `http` middlewares wrap every request, registered so
`CORSMiddleware` is outermost and a short-circuited `413`/`429` still carries CORS
headers:

- **`security_headers`** sets `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Permissions-Policy: geolocation=() camera=() microphone=()`, and a
  `Content-Security-Policy` of `default-src 'none'; frame-ancestors 'none'` for
  the API (a looser CSP for the `/docs` paths, which don't exist in prod).
  `Strict-Transport-Security` is added only when `ENVIRONMENT=production`.
- **`limit_body_size`** rejects a request whose `Content-Length` exceeds
  `MAX_BODY_BYTES` (4 MiB) with `413` before the body is read.
- **`global_rate_limit`** puts a coarse per-IP ceiling
  (`GLOBAL_RATE_LIMIT_PER_MINUTE`, 600) on *mutating* methods only, on top of the
  tight per-endpoint auth limits from M8. Reuses the M8 fixed-window counter.
- **`on_mutation`** (unchanged from M7) emits live-update frames.

A registered `Exception` handler logs the traceback server-side and returns a
flat `{"detail": "Internal server error"}` — no stack traces over the wire.
`/docs`, `/redoc`, `/openapi.json` are disabled when `ENVIRONMENT=production`.
CORS `allow_methods` / `allow_headers` are now explicit lists, not `*`.

**Config guard.** `Settings.model_post_init` already refused a weak `JWT_SECRET`
in production; it now also refuses the *other* dev conveniences when
`ENVIRONMENT=production` — a `sqlite://` database, a `fakeredis://` URL, or
`CELERY_EAGER=true`. All of them are safe, deliberate defaults for local dev
(ADR-0004/0018/0019) and catastrophic in production, so the app fails to boot
rather than start in a degraded state.

**Why middleware, not per-route.** Headers and body/rate ceilings are
cross-cutting; wiring them per-router is how one gets missed. One place to read,
one place to change.

**Why CSRF isn't addressed.** The API is stateless Bearer-token auth — the token
lives in `localStorage` and is attached by an explicit `Authorization` header
(ADR-0007). A browser never attaches it ambiently, so a cross-site form post
can't ride an existing session. The residual risk is XSS reading `localStorage`,
which the `default-src 'none'` CSP and React's default escaping mitigate;
cookie-based auth with `SameSite` would be the move only if we needed
silent-refresh cookies.

**Dependency scanning.** CI runs `pip-audit` (backend) and `npm audit
--audit-level=high` (frontend) as `continue-on-error` steps — visible on every
run, but a fresh advisory in a transitive dependency doesn't block an unrelated
PR. Container image scanning lands with the real Dockerfiles in M13.

**Deferred.** A streaming/chunked body can still exceed the limit (only
`Content-Length` is checked); an SPA-serving layer will need its own CSP with
`script-src 'self'`; secrets management is env-vars for now (a real secret store
is M13). See `SECURITY.md` for the full threat model and the self-pentest
checklist.

## ADR-0023 — Deployment: ECS Fargate + Terraform, one ALB, images from CI

**Decision.** The app runs on **ECS Fargate** in a two-tier VPC: an
internet-facing ALB in public subnets; `api`, `frontend`, `worker` and `beat`
tasks plus RDS Postgres 16 and ElastiCache Redis 7 in private subnets, egress
through a single NAT gateway. **Terraform** (remote state in S3 + a DynamoDB
lock table, bootstrapped by `infra/bootstrap`) provisions all of it. The
**frontend** is the built SPA on nginx — static files only. The **ALB** path-
routes one origin: `/api/*` to the API target group, everything else to the
frontend. Images are built, scanned (Trivy, fails on `CRITICAL`) and pushed to
**ECR** by `.github/workflows/release.yml`, which then registers new task-def
revisions, runs `alembic upgrade head` as a **one-off Fargate task**, and rolls
the services (`aws ecs update-service` + `wait services-stable`). CI assumes an
AWS role via **GitHub OIDC** — no long-lived keys.

**Why ECS Fargate over the alternatives.** App Runner is less to wire but also
less to show and less control (no sidecars, limited networking). EKS is a
Kubernetes control plane to operate and explain for four small services — all
cost, no benefit here. Lightsail/PaaS hides exactly the VPC/ALB/IAM/RDS wiring
that's the point of this milestone. Fargate keeps "no servers to patch" while
still being real ECS + task definitions + target groups + autoscaling — the
vocabulary that transfers.

**Why the ALB path-routes instead of the SPA proxying `/api`.** One origin means
the browser's `Authorization` requests are same-origin, so there's no CORS in
production and the M12 CSP stays tight. `docker-compose.prod.yml` reproduces this
with a tiny `gateway` nginx so local prod-parity behaves identically.

**Why migrations are a separate task, not container start.** N API tasks starting
at once would race on `alembic upgrade`. A single RunTask in the pipeline, gated
before the service roll, makes the schema change atomic and visible in its own
log.

**Why `ignore_changes = [task_definition]` on every service.** Terraform owns
infrastructure; the release pipeline owns which image revision is live. Without
this they'd fight on every `apply`.

**Why Secrets Manager over SSM Parameter Store.** One JSON secret holds the
composed `DATABASE_URL` / `REDIS_URL` / broker URLs / `JWT_SECRET`, injected by
ECS as env vars via the task `secrets` block — never in a task definition, a
tfvars file, or git. The DB and Redis passwords are `random_password`, so no
human ever sees them. `ANTHROPIC_API_KEY` is a second secret created empty with
`ignore_changes` and set out-of-band.

**Why one NAT gateway.** It's the largest single line item (~\$32/mo + data).
One-per-AZ buys AZ-failure resilience for outbound traffic that a portfolio
deploy doesn't need; S3 goes over a gateway endpoint to keep report/upload
bytes off it entirely.

**Local verification limits.** This milestone is infrastructure-as-code: `ci.yml`
gains an `infra` job (`terraform validate` on the stack and the bootstrap,
`shellcheck` on the deploy scripts). An actual `terraform apply` needs an AWS
account and is not part of CI.

**Later additions.** `high_availability` (var, default off) flips RDS to Multi-AZ
and gives Redis a failover replica; `waf_enabled` (var, default on) attaches an
AWS WAF to the ALB (managed common + bad-inputs rule sets + a per-IP rate rule).
Both are `count`/`bool`-gated so they don't disturb the base stack.

**Still deferred.** Blue/green (CodeDeploy) instead of rolling deploys;
CloudFront in front of the SPA; AMP + an ADOT sidecar to scrape ECS into managed
Prometheus (the app already exposes `/metrics`) — each needs a live account to
tune and isn't worth guessing at. The Redis pub/sub WS fan-out consumer that was
listed here shipped in M14 (ADR-0024).

## ADR-0024 — Observability: stdlib logging, `prometheus_client`, Redis WS fan-out

**Decision.** Four pieces, each the smallest thing that works:

- **Structured logs.** A `logging.Formatter` subclass emits one JSON object per
  line (`ts`, `level`, `logger`, `msg`, `request_id`, plus any `extra=`);
  `LOG_JSON` picks JSON vs a readable text format. The prod image sets
  `LOG_JSON=true` and CloudWatch Logs ingests it as-is. No `structlog`, no
  logging framework — a formatter and a `StreamHandler`.
- **Request IDs.** `RequestIDMiddleware` is *pure ASGI* (not
  `BaseHTTPMiddleware`) so it shares a context with Starlette's
  `ServerErrorMiddleware`: it honours an inbound `X-Request-ID` (the ALB adds
  one) or mints a short one, binds it to a `ContextVar`, and echoes it on the
  response. Because the id is still bound when the catch-all handler runs, a
  `500` body carries `request_id` for correlation. `BaseHTTPMiddleware` can't do
  this — it runs downstream in a child task whose context doesn't propagate
  back.
- **Metrics.** The standard `prometheus_client`: a `Counter` and a `Histogram`
  labelled by method, **route template** (`/projects/{project_id}`, not the URL
  — bounded cardinality; unmatched paths collapse to `__unmatched__`) and
  status, incremented in one `@app.middleware`.
  `GET /metrics` renders the default registry (so process/GC collectors come
  for free) and is excluded from its own counters. No auth on `/metrics`: the
  ALB only routes `/api/*` to the API, so it isn't publicly reachable; a
  scraper hits the task IP directly.
- **Error tracking.** `sentry_sdk.init` only when `SENTRY_DSN` is set — the same
  "empty config → no-op" pattern as the Anthropic key. Sentry auto-instruments
  FastAPI/logging once initialised.

**Prometheus + Grafana** run as `docker-compose.observability.yml`, merged onto
the prod stack so they share its network (`prometheus` scrapes `backend:8000`);
Grafana is provisioned with the datasource and one dashboard from
`infra/observability/`. In AWS the app *exposes* `/metrics`; wiring a scraper to
ECS (AMP + an ADOT sidecar, or a Prometheus task with ECS SD) is deferred —
"Compose now, cloud later" per the roadmap. Baseline CloudWatch alarms (ALB
5xx / no-healthy-hosts, ECS + RDS CPU, RDS storage) already ship from
`infra/monitoring.tf`.

**Readiness vs liveness.** `/api/health` stays always-200 (liveness — the ALB
keeps a task in rotation through a blip). New `/api/health/ready` pings the DB
*and* Redis and returns `503` if either is down; uptime monitors and the ECS
deployment circuit-breaker should watch that one.

**WebSocket fan-out (closes ADR-0017's deferral).** Prod runs several API tasks;
`publish()` always mirrored each frame to a Redis channel, but nothing consumed
it. `app.realtime.fanout.run_fanout` now subscribes (async redis client) in each
process and delivers frames tagged with a *different* process `origin` (a
per-process uuid on the `ConnectionManager`) — the publishing process already
delivered to its own sockets directly, so this avoids double-send. It's started
from the lifespan only when Redis is real (`fakeredis`'s pub/sub consumer
blocks), so dev and the test suite stay single-process and never run it; the
delivery-decision function is unit-tested in isolation.

## ADR-0025 — Mobile: an Expo app that shares the API contract, not code

**Decision.** `mobile/` is a standalone Expo (React Native) app — its own
`package.json` and toolchain, a sibling of `backend/` and `frontend/`, not a
workspace package. It uses `expo-router` (file routes in `app/`), TanStack Query,
and an axios client that is a line-for-line port of the web client's
request/response interceptors — same Bearer header, same single-flight refresh
on 401, same `/auth/refresh` contract — changed only where the platform forces
it: tokens go in `expo-secure-store` (async, device keychain) instead of
`localStorage`, and "auth cleared" is a listener set instead of a DOM event.

**Why not a shared `packages/api-client`.** The interceptor body is ~40 lines and
the divergent parts (storage is async on device, sync on web; no `window`) are
exactly the parts a shared module would have to abstract, for two consumers. A
monorepo workspace + build step + a third `tsconfig` project reference is more
moving parts than the duplication removes. The contract is enforced where it
actually matters — the FastAPI response models — and drift shows up as a failed
request, not a silent mismatch. If a third client appears, revisit.

**Scope.** Sign in / register, a dashboard (`/job-tracker/stats` +
`/analytics/overview`), a filterable applications list, and an application detail
screen with inline status changes. Enough to prove the auth flow and the
read/write path on a real device.

**Verification.** No simulator in this environment or in CI, so the gate is
`tsc --noEmit` + `eslint` (a `mobile` job in `ci.yml`). `typedRoutes` is off so
route hrefs typecheck without the `expo start`-generated `.expo/types`.

**Deferred.** Live updates (the WS hook isn't ported); push notifications;
offline cache persistence; the other feature modules; EAS build/submit config.

## ADR-0026 — Calendar: overrides as sparse exception rows, not materialised instances

**Decision.** A recurring event stays one `Event` + an RRULE string. To change or
drop a single instance, `EventOverride` stores one row per exception, keyed by
`(event_id, occurrence_start)` where `occurrence_start` is the *original*
rule-generated start — iCalendar's `RECURRENCE-ID`. NULL override columns inherit
from the parent; `canceled` drops the instance. `expand_occurrences` builds a
`{occurrence_start: override}` map per event and, per generated instance, cancels
/ substitutes accordingly; it then sweeps overrides whose original time fell
outside the query window but whose new time is inside. `PUT .../overrides` upserts
(idempotent per instance), `DELETE /overrides/{id}` reverts.

**Why not materialise the series.** Expanding a recurring event into N stored
rows on creation makes "edit this one" trivial but turns "edit the series",
"extend the recurrence", and storage into problems, and it's how most calendar
schemas rot. Keeping the rule authoritative and overrides sparse matches iCalendar
and means an untouched series is still a single row.

**Why address by `occurrence_start`, not an index.** An index shifts when the
rule or `dtstart` changes; the original datetime is stable and is exactly what
`dateutil.rrule.between(t, t)` can validate against, so a bogus
`occurrence_start` is rejected at write time.

**UI.** The event modal gains a "this occurrence" panel for recurring instances
(reschedule / skip / restore-to-series); the series form is unchanged. Occurrences
carry `occurrence_start` + `overridden` so the month/week views can mark a changed
instance.

## ADR-0027 — Assistant streaming: SSE + a generator over the same loop

**Decision.** `run_chat_stream` is the M10 agentic loop turned into a generator:
each turn calls `client.messages.stream()` instead of `.create()`, forwards
`text_stream` chunks as `{"type": "delta"}`, emits `{"type": "tool"}` before each
tool runs, and ends with `{"type": "done", "tool_calls": [...]}`. `POST
/api/coach/chat/stream` wraps it in a `StreamingResponse` with
`media_type="text/event-stream"`; `ensure_configured()` raises first so a missing
key is still a clean `503` before any bytes are sent. The non-streaming
`POST /coach/chat` stays — the mobile app and the tests use it, and it's the 401
fallback.

**Why SSE, not the WebSocket.** The `/api/ws` channel is a fan-out broadcast
keyed by user; a chat stream is a one-shot response to one request. SSE is a
plain HTTP response the browser reads with `fetch` + `ReadableStream` — no
second connection, no message framing, and it dies with the request.

**Why two code paths, not one.** `run_chat` delegating to `run_chat_stream` would
be DRY but forces `.stream()` on every caller (and every test's fake). Keeping
`run_chat` on `.create()` leaves the simple path simple and the ~25 loop lines
duplicated; the shared `_base_params()` / `execute_tool` / `GAVE_UP` keep them
from drifting. ADR-0020's point stands — the loop is the thing to be able to
explain, and now there are two short ones.

**Frontend.** `sendChatStream` uses `fetch` (axios doesn't surface the body
stream in browsers); a 401 falls back once to the axios call so the refresh
interceptor can run. The chat renders deltas into a trailing bubble with a
blinking caret; tool chips appear as their events arrive.

## ADR-0028 — User timezone: a per-user IANA name, applied only at day boundaries

**Decision.** `User.timezone` holds an IANA name (default `"UTC"`), settable via
`PATCH /auth/me` (validated with `zoneinfo.ZoneInfo`, 422 on a bad name).
Storage stays naive UTC (ADR-0014) — nothing about how timestamps are written
changes. The zone is consulted only where a *calendar day* matters:

- **Analytics** — `resolve_range`'s default end is "today" in the user's zone;
  `_productivity` (overdue cutoff, completed-in-range filter, done-per-week
  buckets) and `_job_search` (applications-per-week) convert each stored
  timestamp with `tz.local_date(dt, name)` before bucketing; `_learning`'s
  "reviews in the last 7 days" counts from the user's today. `_finance` and
  lesson completions are unaffected — those columns are user-entered `date`s
  with no time, so they're already zone-neutral.
- **Assistant** — `SYSTEM_PROMPT`'s "Today's date is …" resolves in the user's
  zone, so "add a task for tomorrow" lands on the right day.

**Why only day boundaries.** The calendar already renders in the viewer's
browser zone (`new Date(iso)`), and money/lessons are dateless. The only place
the server's notion of "which day" leaked was the analytics rollups (the M16
`_utc_today` fix was the same bug, one layer down). Converting every timestamp
everywhere would be churn for no visible gain.

**Deferred.** The daily-digest Celery beat still fires at 07:00 **UTC** for
everyone. Per-user local send time means the beat waking every 15 min and
checking each user's local clock — a real change, and low value until there are
real users.

## ADR-0029 — Render: one self-contained service, no hardcoded hostnames

**Decision.** The Render Blueprint deploys a single Docker web service. A
multi-stage image builds the SPA (`node` stage → `frontend/dist`) and the
FastAPI app serves it: `StaticFiles` on `/assets`, and a catch-all
`GET /{path:path}` (registered after every `/api/*` router, path-traversal
guarded) that returns a real file or falls back to `index.html`. Opt-in via
`STATIC_DIR`; empty → API-only, unchanged. HTML responses get a real CSP
(`_SPA_CSP`: `script-src 'self'`, inline styles, Google Fonts hosts); JSON
responses keep the `default-src 'none'` deny-all.

**Why.** The first blueprint declared two `type: web` services named
`lifeos-api` / `lifeos-web`, wired together with a hardcoded
`https://lifeos-web.onrender.com` in `CORS_ORIGINS` and
`https://lifeos-api.onrender.com` in `VITE_API_URL`. Render (like most PaaS)
hands out **globally unique, first-come** subdomains — both generic names were
already taken by unrelated apps, so a fresh `blueprint apply` could never bind
them and the frontend would have pointed `VITE_API_URL` at a stranger's box.
One same-origin service removes every cross-service URL: no `VITE_API_URL`, no
`CORS_ORIGINS`, nothing to hardcode. Whatever hostname Render assigns is the
app.

**Cost.** The frontend redeploys on every backend change (shared image) and a
CDN no longer fronts the static assets — both irrelevant at this scale, and
`starter` plan + Render's edge cache cover it if that changes. The split
`frontend/Dockerfile` + `backend/Dockerfile` images stay in the repo for a
CDN-fronted or independently-scaled deploy later.
