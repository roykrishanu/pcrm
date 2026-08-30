# Testing

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q          # run tests
./.venv/Scripts/python.exe -m ruff check app tests   # lint
```

Tests run against an in-memory SQLite DB created fresh per test
(`tests/conftest.py::db_session`, `StaticPool` so the whole test shares one
connection). No Postgres/Redis needed to run the suite.

## Coverage so far (`tests/test_auth.py`, `tests/test_leads.py`)

- Organization registration (incl. duplicate-slug rejection).
- Login success, wrong-password (generic error, no enumeration), unknown
  email (same generic error), account lockout after 5 failures.
- Refresh token rotation, and that a used-up old refresh token is rejected.
- Protected-route auth enforcement (401 with no token).
- Lead CRUD, pipeline status change + activity timeline, scoring on
  activity, soft delete (deleted lead 404s afterward).
- **Tenant isolation / IDOR**: org B gets 404 (not 403) reading org A's lead
  by ID, and org A's lead never appears in org B's list.

## Gaps (do before calling auth/RBAC "done")

- No test yet exercises a non-owner role actually being denied a permission
  (needs the user-invite endpoint, which isn't built) — `test_viewer_role_
  cannot_create_lead` currently only proves the owner path works and
  documents this gap inline.
- No email-verification-token-success test (only the failure path is
  covered) — needs a way to intercept the token from the console email
  backend in tests.
- No 2FA tests (feature not built).
- No load/concurrency tests.

## Adding a test for a new endpoint

1. Register + log in an org via the `_register_and_login` helper pattern in
   `tests/test_leads.py`.
2. Assert the happy path.
3. Assert the 401 (no auth) and 404/403 (cross-tenant or missing-permission)
   paths — every new tenant-scoped endpoint needs both.
