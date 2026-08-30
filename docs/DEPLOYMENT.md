# Deployment

## Local (Docker)

```bash
cp .env.example .env   # set a real SECRET_KEY
docker compose up --build
```

Services: `postgres`, `redis`, `backend` (runs `alembic upgrade head` then
`uvicorn`), `worker` (Celery), `frontend`.

## Production checklist

- [ ] `SECRET_KEY` is a real random value (`python -c "import secrets; print(secrets.token_urlsafe(64))"`),
      not the example placeholder, and comes from a secret manager / env var —
      never committed.
- [ ] `ENV=production` (disables `/docs`).
- [ ] `DATABASE_URL` points at a real Postgres instance with connection pooling
      appropriate to your instance count (`pool_size`/`max_overflow` in
      `app/db/session.py`).
- [ ] `CORS_ORIGINS` restricted to your real frontend origin(s), not `*`.
- [ ] TLS terminated in front of the backend (load balancer / reverse proxy).
- [ ] `EMAIL_BACKEND=smtp` with real `SMTP_*` credentials (or swap
      `app/services/email_service.py` for a provider SDK) — the `console`
      backend only logs, it does not deliver.
- [ ] Redis is a managed/persistent instance if rate limiting is moved there
      (see `docs/SECURITY.md` ceiling note — currently in-process, fine for a
      single backend replica only).
- [ ] Backups configured for Postgres (not yet documented/automated here —
      do this before real customer data exists).
- [ ] Run `alembic upgrade head` as a release step, before traffic is
      switched to the new version.

## What's NOT set up yet

CI/CD pipeline file, container registry push, zero-downtime migration
strategy for breaking schema changes, log/metric shipping to an external
observability backend, automated backup jobs. Track these in
`PROJECT_STATUS.md` before declaring the project production-ready per
section 91 of the build spec.
