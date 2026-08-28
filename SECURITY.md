# Security

How LifeOS is defended, what is deliberately out of scope, and the checks run
against it. This is a portfolio project, not a hosted service — there is no bug
bounty and no `security@` inbox. The point of this document is to be able to
walk through the threat model in an interview.

See `DECISIONS.md` ADR-0022 for the security-pass rationale, and ADR-0007
(token storage), ADR-0010 (logic lives in services), ADR-0018 (Redis).

## Threat model

**Assets.** A user's own data across every module (applications, tasks, events,
transactions, courses, flashcards) and their account credentials. Each row is
owned by exactly one user; there is no sharing.

**Trust boundary.** The FastAPI process is the only thing that touches the
database. The SPA is an untrusted client. Every request that reads or writes
user data must present a valid access token, and the query is always filtered
by the token's `sub`.

**In scope**

| Threat | Mitigation |
| --- | --- |
| Broken object-level authorization (IDOR) | Every route resolves a row through a `_*_or_404(db, user, id)` helper that filters on `user_id`; a mismatched owner gets a `404`, not a `403` (no existence oracle). Covered by per-module ownership tests. |
| SQL injection | All queries go through SQLAlchemy Core/ORM with bound parameters. No f-string SQL, no `text()` with interpolation. The one raw `text("SELECT 1")` is the health probe and takes no input. |
| Credential stuffing / brute force | `POST /auth/login` 10/min per IP, `POST /auth/register` 5/min per IP (fixed-window counter in Redis). Passwords hashed with Argon2 (`pwdlib`). |
| Write floods | `GLOBAL_RATE_LIMIT_PER_MINUTE` (600) per IP across all mutating methods, on top of the auth limits. |
| Token replay after logout | `POST /auth/logout` adds the token's `jti` to a Redis denylist; `POST /auth/logout-all` bumps a per-user generation counter carried in every token. `get_current_user` checks both. |
| Stolen refresh token | Refresh tokens are a distinct token type (`typ` claim); an access token can't be used at `/auth/refresh` and vice-versa. Short access TTL (30 min). |
| Stack traces / internals leaking | A catch-all `Exception` handler logs server-side and returns a flat `{"detail": "Internal server error"}`. `/docs`, `/redoc`, `/openapi.json` are off in production. |
| Clickjacking / MIME sniffing / referrer leak | `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` on every response. |
| Oversized-payload DoS | Requests declaring `Content-Length` over 4 MiB are rejected with `413` before the body is read. |
| Cross-origin abuse | CORS allow-list is the configured origin(s) only, with explicit method/header lists (no `*`). |
| Boot in a degraded state | `Settings.model_post_init` refuses to start when `ENVIRONMENT=production` and the JWT secret is weak/default, the database is SQLite, Redis is `fakeredis`, or Celery is eager. |
| Secrets in the repo | Config is entirely env-driven; `.env` is gitignored; the committed `.env.example` has only placeholders. `pip-audit` + `npm audit` run in CI. |

**Out of scope / accepted risk**

- **CSRF.** Auth is a stateless Bearer token attached by an explicit
  `Authorization` header, never an ambient cookie, so a cross-site request
  cannot ride a logged-in session. No anti-CSRF token is needed. This would
  change if silent-refresh moved to a cookie.
- **XSS reading `localStorage`.** The access token lives in `localStorage`
  (ADR-0007), so a script-injection bug would expose it. Mitigated by React's
  default escaping and a `default-src 'none'` CSP on API responses; not
  eliminated. The SPA's own serving layer (M13) needs its own `script-src
  'self'` CSP.
- **Streaming body over the limit.** Only `Content-Length` is checked; a
  chunked request with no declared length isn't capped at the middleware.
- **Multi-tenant isolation at the DB layer.** One database, filtered in the
  app. No row-level security.
- **Rate limiting is per-IP and fixed-window.** A botnet or a boundary burst
  can exceed the nominal rate by ~2x. A sliding window / per-account limit is
  the upgrade if it matters.
- **No account lockout, no MFA, no email verification, no password-reset flow.**
- **Secrets management**: in AWS every credential is in Secrets Manager, injected
  by ECS as an env var and never written to a task definition, Terraform state,
  or git (ADR-0023). Local dev still uses a plain `.env`.
- **WAF / network-layer DoS**: not in front of the ALB yet (deferred). Container
  images are scanned by Trivy in the release pipeline (fails on `CRITICAL`).
- **Multi-task realtime**: production runs several API tasks; the in-process
  WebSocket `ConnectionManager` only pushes to clients on the same task until
  the Redis pub/sub fan-out consumer lands (ADR-0017). Not a confidentiality
  issue — just missed live updates.

## Self-pentest checklist

Run against a local instance. All of these are exercised by
`backend/tests/test_security.py`, `test_auth.py`, and the per-module ownership
tests unless noted.

- [x] Fetch another user's application / task / event / transaction / course by
      guessing its id → `404`.
- [x] Reuse an access token after `POST /auth/logout` → `401`.
- [x] Reuse every outstanding token after `POST /auth/logout-all` → `401`.
- [x] Present a refresh token to a normal endpoint, or an access token to
      `/auth/refresh` → `401`.
- [x] 11 logins in a minute from one IP → `429` with `Retry-After`.
- [x] Exceed the global mutation ceiling → `429`.
- [x] `POST` a body larger than 4 MiB → `413`.
- [x] Force an unhandled exception in a handler → `500` with
      `{"detail": "Internal server error"}` and no traceback in the body.
- [x] Every response carries the security headers; HSTS only in production.
- [x] Boot with `ENVIRONMENT=production` and any dev default
      (secret / SQLite / fakeredis / eager Celery) → the app raises on startup.
- [ ] Manual: confirm `/docs` and `/openapi.json` 404 when
      `ENVIRONMENT=production` (covered by construction, not a test).
- [ ] Manual: `pip-audit` and `npm audit --audit-level=high` are clean
      (also a CI step).

## Reporting

This is a learning project with no production deployment. If you're reviewing it
and spot something, open an issue on the repo.
