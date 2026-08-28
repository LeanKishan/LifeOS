# LifeOS Roadmap

Built one milestone at a time. Each milestone is a vertical slice that ends
with something running, tested, and committed. Everything from the original
brief is in here — nothing is dropped, it is sequenced.

Legend: `[x]` done · `[~]` in progress · `[ ]` planned

---

## M0 — Foundation
- [x] Monorepo, git, `.gitignore`
- [x] FastAPI skeleton (`/`, `/api/health`), app factory, CORS
- [x] Config via `pydantic-settings`
- [x] SQLAlchemy 2.0 engine + session dependency
- [x] Alembic wired to model metadata
- [x] Password hashing + JWT helpers (argon2, access/refresh)
- [x] React + Vite + TS + Tailwind + Router + TanStack Query
- [x] API client with auth-header interceptor
- [x] `docker-compose.yml` — db, redis, backend, frontend
- [x] GitHub Actions CI — lint, type-check, migrate + test on real Postgres, build
- [x] Local dev on SQLite (no local virtualization for Docker — see ADR-0004)
- [ ] `docker compose up` verified end to end (blocked on Docker/WSL2)

## M1 — Authentication
- [x] `User` model + first Alembic migration (batch mode: applies on SQLite + Postgres)
- [x] `register` / `login` / `refresh` / `me` endpoints (logout is a client-side token clear)
- [x] `get_current_user` / `get_current_active_user` dependencies, protected-route pattern
- [x] Frontend: auth context, login/register pages, route guards, silent refresh on 401
- [x] Tests: register/login/refresh happy paths + wrong password, garbage/expired/wrong-type token
- [x] Production guard: app refuses to boot with a weak or default `JWT_SECRET`
- [ ] Refresh-token rotation + revocation list (Redis) — deferred to M8
- [ ] OAuth login (Google)
- [ ] Role-based permissions — `is_superuser` column exists; enforcement helper comes later

## M2 — Job Tracker (first feature module)
- [x] Models: Company, Application, Interview, Contact (user-scoped, cascade delete)
- [x] CRUD endpoints, all scoped to the current user
- [x] Applications filter by `?status=` and `?sort=`
- [x] Status pipeline: wishlist → applied → assessment → interviewing → offer →
      accepted / rejected / withdrawn
- [x] Salary fields + `/job-tracker/stats` (by-status, active, response rate, offer rate)
- [x] Auto-create-or-link company by name (case-insensitive) when adding an application
- [x] Frontend: board + table views, create modal, detail drawer (inline edit +
      interviews), dashboard stat cards
- [x] Tests: 15 integration tests — ownership, auto-company, partial patch, filter,
      interview cascade, stats aggregation
- [ ] Resume / file upload (local disk now, S3 later) → M2.1
- [ ] Contacts UI — backend + tests done, no screen yet → M2.1
- [ ] Drag-and-drop between board columns → folded into M3 (Kanban)
- [ ] Pagination — list is unbounded for now

## M3 — Project Management (Kanban)
- [x] Models: Project, BoardColumn, Task, Subtask, Label (per-project), TaskComment
- [x] User-defined columns; new project seeds "To Do / In Progress / Done"
- [x] Dense 0..n-1 ordering; `POST /tasks/{id}/move` renumbers source + target,
      clamps out-of-range position; column reorder endpoint
- [x] Priorities (StrEnum), due dates, per-project labels (PUT replaces the set)
- [x] Frontend: @dnd-kit Kanban board with optimistic drag-and-drop, task modal
      (description, priority, due, subtasks, labels, comments), project list
- [x] Tests: 16 — default columns, positions, within/cross-column move, clamp,
      delete gap-close, column reorder, subtask counts, label rules, ownership
- [ ] Attachments → later (with file upload in M2.1)
- [ ] Board filters (by label / priority / assignee) → later
- [ ] Optimistic reorder is best-effort (server position semantics win on refetch);
      fractional/lexo-rank ordering is the scale answer

## M4 — Calendar
- [x] Models: Event (RRULE string, not a rules table), Reminder
- [x] Recurring events expanded with dateutil; `GET /occurrences?from=&to=`
      returns instances clipped to the window (capped 400 days / 750 instances)
- [x] Reminders (data + CRUD; delivery is M9)
- [x] Optional SET NULL links from an event to a project / task / application,
      validated on write
- [x] All datetimes naive UTC (ADR-0014); API takes an offset and converts
- [x] Frontend: month + week views, prev/today/next nav, event modal with
      repeat presets, dashboard "Upcoming" list
- [x] Tests: 15 — time/RRULE validation, foreign link, single/partial overlap,
      weekly COUNT, DAILY UNTIL, window clipping, duration, sort, range cap
- [ ] Per-occurrence overrides (move/cancel one instance) → later
- [ ] Non-UTC display / user timezone setting → later

## M5 — Finance
- [x] Models: Account, Category (typed), Transaction (integer cents), Budget
      (unique per user+category+month), Bill
- [x] `GET /summary?month=` — grouped-SUM rollup: income/expense/net, savings
      rate, per-category spent vs budget (over flag), uncategorized, bills total
- [x] Account balance = starting + Σincome − Σexpense (computed)
- [x] Filtered transaction list (account/category/kind/date range, limit/offset)
- [x] CSV import (multipart), auto-creates categories, per-row error report
- [x] Frontend: month summary cards, spending-vs-budget bars, budget editor,
      accounts strip, transactions table with kind filter, CSV import button
- [x] `PRAGMA foreign_keys=ON` for SQLite so ON DELETE behaves like Postgres
- [x] Tests: 14 — amount validation, balance, filters, summary math + month
      boundary + budget-vs-actual, budget upsert, CSV import, cascade/SET NULL
- [ ] Transfers (account-to-account) → later
- [ ] Recurring-transaction generation from bills → M9 (Celery)

## M6 — Learning Management
- [x] Models: Course, Lesson (ordered, completed), Note, Flashcard (SM-2 state),
      LearningGoal
- [x] SM-2 spaced repetition (`apply_sm2`, unit-tested pure function)
- [x] `GET /learning/review` due-today queue + `POST /flashcards/{id}/review`
- [x] Course progress (lessons_completed / lesson_count) + flashcards_due count
- [x] Frontend: course list with progress bars, course detail (lessons /
      flashcards / notes), flashcard review session (flip + Again/Hard/Good/Easy)
- [x] Tests: 15 — SM-2 (good/fail/ease-floor/bad-quality), review queue + scope,
      progress, lesson complete/uncomplete, reorder, cascade
- [ ] Quizzes → later
- [ ] Goal progress % → later

## M7 — Real-time
- [x] `GET /api/ws?token=` — JWT-authed push channel; `ConnectionManager` keyed
      by user (in-process; Redis fan-out is M8 / ADR-0017)
- [x] One `http` middleware emits `{type: <channel>}` after any 2xx mutation
      under a feature prefix — no per-route wiring
- [x] Frontend `useLiveUpdates` hook: reconnecting socket, invalidates the query
      key named by each frame; "● live" indicator in the header
- [x] Collaborative updates: a task moved from one client updates every other
      client's board with no reload
- [x] Tests: 6 — manager fan-out is user-scoped, disconnect, WS auth accept/
      reject, mutation delivers a frame
- [ ] Toast notifications (need a source — arrives with M9 reminders)

## M8 — Redis, hard
- [x] Client: `fakeredis://` dev default (no install), real Redis in CI/Compose/prod
- [x] Token revocation: per-`jti` denylist (`/auth/logout`) + per-user generation
      counter (`/auth/logout-all`); `get_current_user` enforces both
- [x] Rate limiting: fixed-window per-IP dependency, 10/min login, 5/min register
- [x] Response cache: `/finance/summary` + `/job-tracker/stats`, versioned keys,
      busted by the M7 mutation middleware
- [x] Frontend: Log out calls the server (real revoke), "everywhere" button,
      429 handled on the login form
- [x] Tests: 6 — logout revokes access + refresh, logout-all, login/register 429,
      cache hit + bust
- [ ] Idempotency keys for mutations → later
- [ ] Redis pub/sub WS fan-out consumer → with the multi-worker deploy (M13)

## M9 — Background processing (Celery)
- [x] Celery app; `task_always_eager` in dev/tests (no broker), `worker` + `beat`
      services in Compose against a Redis broker
- [x] `generate_finance_report` — reportlab PDF -> Redis (7-day TTL) -> notification;
      `POST /finance/reports` enqueues, `GET /finance/reports/{month}` streams it
- [x] `dispatch_due_reminders` (beat 60s) -> `{type: notification}` WS frames,
      at-most-once via a Redis SET NX key per (reminder, occurrence)
- [x] `send_daily_digest` (beat 07:00) -> one summary notification per user
- [x] Frontend: toast tray (`<Toaster>`) fed by notification frames; "Report PDF"
      button on the finance page
- [x] Tests: 5 — report renders %PDF + notifies, endpoint enqueues+serves,
      reminder fires once then dedups, digest
- [ ] Email delivery (notifications are in-app only for now)
- [ ] Recurring-event materialization → deferred (calendar expands on the fly)

## M10 — AI Assistant
- [x] Manual tool-use loop against claude-opus-5 (adaptive thinking, effort=medium,
      6-iteration cap)
- [x] 6 tools calling the service layer directly (get_agenda, get_finance_summary,
      list_projects, create_task, create_event, add_flashcard), all user-scoped
- [x] `execute_tool` is fail-soft — bad input comes back as `"error: ..."`
- [x] `POST /api/coach/chat`, stateless; no API key -> 503, rest of the app unaffected
- [x] Frontend: chat panel with tool-call badges, suggestion chips, 503 notice
- [x] Tests: 7 (Anthropic client mocked) — loop, tool round-trip, give-up,
      real task creation, tool errors, endpoint 200/503
- [ ] Streaming responses → polish
- [ ] Per-user rate limit / spend cap on the endpoint → with the deploy

## M11 — Analytics
- [x] `Task.done` + `completed_at` (8th migration) so productivity is measurable
- [x] `GET /analytics/overview?from=&to=` (default 90d, cap 366d): productivity
      (completion rate, avg cycle days, overdue, priority split, done-per-week),
      finance (net-per-month, top categories), learning (maturity buckets,
      reviews last 7d, lessons-per-week), job funnel + apps-per-week
- [x] SQL GROUP BY for the cardinal splits; time buckets in app code (ADR-0021)
- [x] `GET /analytics/export.{csv,pdf}`
- [x] Frontend: date-range analytics page, inline bar / diverging-bar charts,
      CSV + PDF download; task "done" checkbox in the Kanban modal + card
- [x] Tests: 9 — completion + cycle, overdue, monthly net, maturity, funnel,
      range 422, user scoping, CSV/PDF
- [ ] Richer charts (stacked, trend lines) → polish; dataviz pass deferred

## M12 — Security pass
- [x] Security headers on every response (nosniff, DENY, no-referrer,
      Permissions-Policy, `default-src 'none'` CSP; HSTS in prod only)
- [x] 4 MiB request-body limit (`413`), coarse per-IP write rate limit (`429`)
- [x] Generic `500` handler — no stack traces on the wire; `/docs` off in prod
- [x] CORS tightened to explicit method / header lists
- [x] Production config guard extended: refuses dev SQLite / fakeredis / eager
      Celery / weak secret when `ENVIRONMENT=production`
- [x] `pip-audit` + `npm audit` in CI (informational, `continue-on-error`)
- [x] `SECURITY.md` — threat model + self-pentest checklist; ADR-0022
- [x] Tests: 5 — headers present, oversized body, global rate limit, reads
      unthrottled, unhandled error stays generic (+ config guard tests)
- [ ] CSRF: not applicable — Bearer-token auth, no ambient cookie (documented)
- [ ] Streaming/chunked body isn't capped (only `Content-Length`) → later
- [ ] Sliding-window / per-account rate limits → later
- [ ] Container image scanning → M13 (with the real Dockerfiles)
- [ ] Real secret store (env vars for now) → M13

## M13 — Deployment (AWS)
- [x] Multi-stage Dockerfiles (`dev` / `build` / `prod` targets); `prod` is
      non-root, gunicorn + uvicorn workers, an entrypoint that dispatches
      serve / migrate / worker / beat
- [x] Frontend `prod` image: built SPA on nginx (static only, `/healthz`)
- [x] `docker-compose.prod.yml` — prod images + a `gateway` nginx that mirrors
      the ALB's `/api/*` vs `/*` path routing
- [x] Terraform stack in `infra/`: VPC (2 AZ, 1 NAT, S3 endpoint), ALB
      (optional ACM/Route53), RDS Postgres 16, ElastiCache Redis 7, S3 assets
      bucket, ECR, 4 ECS services + API CPU autoscaling, CloudWatch alarms
- [x] Secrets in Secrets Manager (random DB/Redis/JWT), injected via task
      `secrets`; nothing sensitive in state or git
- [x] `infra/bootstrap` for the remote-state bucket + lock table
- [x] GitHub OIDC deploy role; `release.yml` builds + Trivy-scans + pushes to
      ECR, runs migrations as a one-off task, rolls the services
- [x] CI `infra` job: `terraform validate` (stack + bootstrap) + `shellcheck`
- [ ] Actual `terraform apply` to a live account (needs AWS credentials)
- [ ] Blue/green via CodeDeploy; multi-AZ RDS + Redis replica → later
- [ ] WAF on the ALB, CloudFront in front of the SPA → later
- [ ] Redis pub/sub WS fan-out consumer — now needed (multiple API tasks) → M14

## M14 — Monitoring
- [ ] Structured logging, request metrics
- [ ] Prometheus + Grafana in Compose, then in cloud
- [ ] Error tracking, uptime checks

## M15 — Mobile (React Native)
- [ ] Shared API client, auth, dashboard + job tracker screens
