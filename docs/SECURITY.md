# Security Model

## Authentication

- Passwords hashed with bcrypt (via passlib). Minimum 10 chars, upper+lower+digit
  required (`app/schemas/auth.py::validate_password_strength`).
- Login failure returns the identical error/message for "no such user" and
  "wrong password" (no account enumeration via login).
- 5 consecutive failures locks the account for 15 minutes
  (`LOGIN_LOCKOUT_THRESHOLD` / `LOGIN_LOCKOUT_MINUTES`).
- Login is rate-limited per-IP and per-email (`LOGIN_RATE_LIMIT_PER_MINUTE`,
  in-memory — see ceiling note below).
- Access tokens are short-lived JWTs (15 min); refresh tokens are opaque,
  hashed at rest, rotated on every refresh call, and revocable individually
  or all-at-once (logout / logout-all-devices).
- Password reset and email verification tokens are single-use, hashed at
  rest, short-expiry, and the reset flow revokes all existing sessions.
- 2FA: schema field (`users.totp_secret_encrypted`, `is_2fa_enabled`) exists;
  enrollment/verification endpoints are NOT built yet — tracked in
  `PROJECT_STATUS.md`.

## Authorization / tenant isolation

- `organization_id` is NEVER read from the request. It is derived server-side
  from the authenticated user via `get_current_org_id`
  (`app/core/deps.py`). Every service function takes it as an explicit
  parameter and filters every query by it.
- RBAC via `require_permission(key)` — see `app/core/permissions.py` for the
  catalog and `docs/ARCHITECTURE.md` for the model.
- IDOR/BOLA: cross-tenant reads return 404 (existence not confirmed), not
  403 — see `tests/test_leads.py::test_tenant_isolation_cannot_read_other_org_lead`.
- Soft delete: leads (and future CRM entities) use `deleted_at`, not a hard
  DELETE, so audit history and recovery remain possible. Audit logs are
  append-only — no update/delete route exists for them at all.

## Input validation / mass assignment

- Every write endpoint takes a Pydantic request schema, never the ORM model
  directly — a client can only set fields the schema explicitly allows.
- Password strength, email format (`EmailStr`), and slug format are
  validated at the schema layer, not just in the frontend.

## Error handling

- All errors funnel through `app/core/errors.py` into the standard envelope
  (`{"error": {"code", "message", "request_id"}}`). Unhandled exceptions are
  logged with a `request_id` and returned as a generic 500 — stack traces
  never reach the client.

## Logging

- Structured JSON logs (`structlog`) include `request_id`, method, path,
  status, duration. Passwords, tokens, and secrets are never logged — only
  their presence/absence, never their value.

## Known ceilings (ponytail-flagged, upgrade before scaling)

- **Rate limiting is in-process** (`app/core/rate_limit.py`) — fine for one
  backend replica; won't share counters across multiple instances. Upgrade
  path: Redis `INCR`+`EXPIRE` (Redis is already configured via `REDIS_URL`).
- **No Postgres row-level security** — tenant isolation is enforced only in
  the service layer. Fine as long as every query goes through the service
  layer (it currently does); RLS would add defense-in-depth against a future
  raw-query mistake.
- **Lead scoring rules are a hardcoded dict**, not per-organization
  configurable yet (`app/services/scoring_service.py`).

## Not yet implemented (do not claim these work)

CSRF protection (N/A yet — no cookie-based session, bearer tokens only, but
revisit if cookies are introduced for the frontend), file upload
scanning/validation, webhook signing, API keys, 2FA enrollment flow, audit
log export/retention policy, encryption-at-rest for `totp_secret_encrypted`
(field exists, encryption not wired).
