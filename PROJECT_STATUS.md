# Project Status

Last updated: 2026-08-30

## Completed

**Phase 1 — Architecture/infra**
- Repo scaffolded: `backend/` (FastAPI), `frontend/` (Next.js 16, TS, Tailwind), `docker-compose.yml`, `Dockerfile`s, `.env.example`, `.github/workflows/ci.yml`.
- Config via `pydantic-settings` (`backend/app/core/config.py`) — no hardcoded secrets, `SECRET_KEY` required with no default.
- Structured JSON logging + request-id middleware + security headers (`backend/app/core/middleware.py`).
- Consistent error envelope (`backend/app/core/errors.py`).
- `/health` and `/ready` (DB connectivity check) endpoints.
- Alembic wired (hand-written migrations, not autogenerate — see `docs/DATABASE.md`): `0001_initial` (all tables), `0002_seed_permissions`.

**Phase 2 — Auth / Users / Orgs / RBAC**
- Multi-tenant data model: `organizations`, `users` (org-scoped, nullable org for super admins), `teams`, `roles` (per-org, 6 seeded defaults: owner/admin/manager/agent/sales_executive/viewer), `permissions` (fixed platform catalog), `role_permissions`.
- Auth: register-organization (creates org + owner + seeds roles/statuses), login (generic error on failure, 5-strike lockout, per-IP and per-email rate limiting), JWT access tokens (15 min) + rotating opaque refresh tokens (30 days, hashed at rest, `sessions` table = device list), logout / logout-all-devices, password reset (single-use hashed token, revokes all sessions on success), email verification (console-logged in dev), change-password.
- RBAC enforced server-side via `require_permission(key)` dependency — see `backend/app/core/permissions.py` for the full capability catalog.
- Tenant isolation: `organization_id` is derived exclusively from the authenticated JWT (`get_current_org_id`), never accepted from the client. Verified by test (`test_tenant_isolation_cannot_read_other_org_lead`) — cross-tenant reads return 404, not 403.
- Audit log (`audit_logs`, append-only, no update/delete route) — records org creation, login, lead create/update/status-change/delete.

**Phase 3 slice — Leads**
- `lead_statuses` (per-org customizable pipeline, seeded with the 12 default stages), `leads`, `lead_activities` (append-only timeline).
- Full CRUD + pipeline status-change endpoint + activity timeline + activity-triggered scoring (`backend/app/services/scoring_service.py` — fixed point table per spec section 12, clamped 0–100; temperature derived from score).
- Soft delete on leads (`deleted_at`, excluded from all queries).

**Frontend**
- Next.js App Router, TypeScript, Tailwind, mobile-first (bottom nav, full-width forms, bottom sheet for "add lead", 44px+ touch targets).
- Pages: `/login`, `/register` (create org), `/leads` (list + search + quick-add), `/leads/[id]` (detail: call/WhatsApp/email quick actions, status dropdown, score/temperature, note + timeline), `/account` (profile + sign out).
- Bearer-token API client with automatic refresh-on-401 (`src/lib/api.ts`).
- Verified end-to-end in-browser: register → login → create lead → view detail → add note → timeline updates.

## Tests

16/16 passing (`backend/tests/`), lint clean (`ruff`), frontend lints and builds clean (`npm run lint && npm run build`). See `docs/TESTING.md` for coverage detail and gaps.

```bash
cd backend && ./.venv/Scripts/python.exe -m pytest -q && ./.venv/Scripts/python.exe -m ruff check app tests
cd frontend && npm run lint && npm run build
```

## Known issues / gaps (be honest, not aspirational)

- **RBAC test gap**: no test yet proves a non-owner role is actually denied a permission — needs the user-invite endpoint (not built) to create a second user with a restricted role. `test_viewer_role_cannot_create_lead` only documents this gap.
- **2FA**: DB fields exist (`totp_secret_encrypted`, `is_2fa_enabled`); no enrollment/verification endpoints.
- **Rate limiting is in-process** (single backend replica only) — see `docs/SECURITY.md` ceiling note.
- **Lead scoring rules are hardcoded**, not per-org configurable yet.
- **Frontend auth tokens live in localStorage**, not httpOnly cookies — acceptable for now, documented upgrade path in `src/lib/api.ts`.
- **No CI has actually run** (workflow file written, never executed on a remote — this repo has no GitHub remote yet).
- Email delivery is console-only in dev (`EMAIL_BACKEND=console`); SMTP path is implemented but untested against a real server.

## Blocked

Nothing currently blocked. Docker was not available in this dev environment to smoke-test `docker-compose.yml`/`Dockerfile`s directly — they're written to the same patterns as the working local (non-Docker) setup but haven't been built/run. Verify with `docker compose up --build` when Docker is available.

## Next task (exact, in priority order per the build spec)

1. **User management endpoints** (`/users`: invite, list, update, deactivate) + accept-invite flow — this unblocks real RBAC test coverage (item above) and is needed before Teams/assignment features mean anything.
2. **Properties** (Phase 4): model + CRUD + media + search, mirroring the Lead slice's patterns (tenant-scoped service, soft delete, audit log, permission-gated routes, activity-style history for status changes).
3. **Property matching engine** (Phase 4b) once properties exist.
4. **Customers / Owners / Developers / Visits** (Phase 5).
5. Continue down the phase order in the original spec (Deals → Communication → Reports → Automation → AI → PWA → Billing → hardening).

## Commands to continue

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q            # verify no regressions before starting new work
./.venv/Scripts/python.exe -m alembic upgrade head # apply migrations to your dev DB
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --app-dir backend

cd frontend
npm run dev
```

When adding a new entity, follow the Lead slice as the template: model in
`app/models/`, schema in `app/schemas/`, service in `app/services/`
(tenant-scoped functions, audit log calls), router in `app/api/v1/`
(permission-gated), hand-written Alembic migration, tests covering
happy-path + 401 + cross-tenant 404.
