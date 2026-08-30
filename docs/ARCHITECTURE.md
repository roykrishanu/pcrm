# Architecture

## System overview

```
Next.js frontend  --HTTPS-->  FastAPI backend  --async SQLAlchemy-->  PostgreSQL
                                     |
                                     +--> Redis (rate limiting, cache, Celery broker/backend)
                                     +--> Celery workers (email, exports, webhooks, reminders)
```

## Backend architecture

`backend/app/`:

- `core/` — config (`config.py`), JWT + password hashing (`security.py`), auth
  dependencies (`deps.py`), permission catalog (`permissions.py`), error
  envelope (`errors.py`), request-id/logging/security-header middleware
  (`middleware.py`), rate limiting (`rate_limit.py`).
- `db/` — engine/session (`session.py`), declarative base + mixins
  (`base.py`: `UUIDPKMixin`, `TimestampMixin`, `SoftDeleteMixin`,
  `TenantMixin`), seed routines (`seed.py`).
- `models/` — SQLAlchemy ORM models, one module per aggregate.
- `schemas/` — Pydantic request/response models. Never reuse ORM models as
  API schemas — this is the boundary that prevents mass assignment.
- `services/` — business logic. Routes are thin; every rule (lockout,
  tenant scoping, scoring, audit) lives here so it's unit-testable without
  going through HTTP.
- `api/v1/` — FastAPI routers. Each route: validate input (schema) → resolve
  identity (`get_current_user`/`get_current_org_id`) → check permission
  (`require_permission`) → call service → return schema.
- `workers/` — Celery app and background tasks.

Request flow for a protected write (e.g. `POST /api/v1/leads`):
1. `get_current_org_id` decodes the JWT, loads the `User` row, confirms the
   user and their organization are active. `organization_id` comes from
   nowhere else.
2. `require_permission("leads.create")` checks the user's role's permission
   set (or `is_super_admin` / `owner` bypass).
3. `lead_service.create_lead` runs the actual DB write, scoped to that
   `organization_id`, and writes an audit log row in the same transaction.

## Multi-tenancy

Organization is the tenant root. Every tenant-owned table carries
`organization_id` via `TenantMixin`. There is currently no Postgres
row-level-security policy — isolation is enforced entirely in the service
layer by always filtering on server-derived `organization_id`. See
`docs/SECURITY.md` for the tenant-isolation test coverage and the RLS
upgrade path.

## RBAC

Permissions are a fixed, platform-wide catalog of capability strings
(`app/core/permissions.py`, seeded once via Alembic). Roles are
per-organization rows (`is_system=True` roles are seeded automatically when
an organization is created) holding a set of permissions. A user has exactly
one role. `owner` and `is_super_admin` bypass the permission check entirely
(full access); everyone else must have the specific permission key.

## Auth

- Access token: short-lived (15 min default) JWT, stateless, carries
  `user_id`/`org_id`/`role`/`is_super_admin` at issue time.
- Refresh token: long-lived (30 days) random opaque string. Only its SHA-256
  hash is stored (`sessions` table = one row per logged-in device). Rotated
  on every use. Enables "logout everywhere" and a device list.
- Password reset / email verification: same hash-only opaque-token pattern
  (`one_time_tokens`), single use, short expiry.

## Lead pipeline & scoring

`lead_statuses` is a per-organization table (customizable pipeline stages,
seeded with the 12 default stages from the spec). `leads.status_id` FKs into
it. `lead_activities` is an append-only timeline; each activity type can
carry a fixed point delta (`app/services/scoring_service.py`) applied to
`leads.score`, clamped to [0, 100]. Temperature (cold/warm/hot/very_hot) is
derived from score, not stored.

## What's NOT built yet

See `PROJECT_STATUS.md` — properties, matching, visits, deals, documents,
communication providers, automation engine, webhooks, reports/analytics,
super-admin, billing, and the full frontend are still pending. This document
will grow a section per subsystem as each ships.
