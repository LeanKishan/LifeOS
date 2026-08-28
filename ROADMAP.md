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
- [ ] Models: Event, RecurrenceRule, Reminder
- [ ] Recurring events (RRULE), reminders
- [ ] Link events to projects/applications
- [ ] Frontend: month/week views

## M5 — Finance
- [ ] Models: Account, Transaction, Category, Budget, Bill, Subscription
- [ ] Monthly rollups, savings rate, budget-vs-actual (SQL aggregation)
- [ ] CSV import
- [ ] Frontend: charts, budget editor

## M6 — Learning Management
- [ ] Models: Course, Lesson, Note, Flashcard, Quiz, LearningGoal
- [ ] Spaced-repetition review queue
- [ ] Progress bars per subject
- [ ] Frontend: course view, flashcard review

## M7 — Real-time
- [ ] WebSocket endpoint + connection manager
- [ ] Live dashboard updates, notifications
- [ ] Collaborative task updates
- [ ] Frontend: socket hook, toast notifications

## M8 — Redis, hard
- [ ] Dashboard cache with invalidation
- [ ] Rate limiting middleware
- [ ] Session / token-revocation store
- [ ] Idempotency keys for mutations

## M9 — Background processing (Celery)
- [ ] Worker + beat in Compose
- [ ] Monthly financial report → PDF → notification
- [ ] Email reminders, recurring-event materialization
- [ ] Task status surfaced in the UI

## M10 — AI Assistant
- [ ] Tool schema over existing API (read tasks, budgets, applications; create task/event)
- [ ] Chat endpoint with tool-calling loop + guardrails
- [ ] "What's due today?", "Create a task Friday 6pm", "Am I over budget?"
- [ ] Frontend: assistant panel, streamed responses

## M11 — Analytics
- [ ] Aggregation queries, date-range filters
- [ ] Productivity + finance + learning dashboards
- [ ] CSV / PDF export

## M12 — Security pass
- [ ] Input validation review, security headers, CSRF where relevant
- [ ] Rate limiting on auth, secrets management
- [ ] Dependency + container scanning in CI
- [ ] Self-pentest notes

## M13 — Deployment (AWS)
- [ ] Production Dockerfiles (multi-stage), migrations on release
- [ ] Managed Postgres + Redis, load balancer, object storage
- [ ] IaC (Terraform), deploy from CI

## M14 — Monitoring
- [ ] Structured logging, request metrics
- [ ] Prometheus + Grafana in Compose, then in cloud
- [ ] Error tracking, uptime checks

## M15 — Mobile (React Native)
- [ ] Shared API client, auth, dashboard + job tracker screens
