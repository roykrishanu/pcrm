# Deployment

## Local (Docker)

```bash
cp .env.example .env   # set a real SECRET_KEY
docker compose up --build
```

Services: `postgres`, `redis`, `backend` (runs `alembic upgrade head` then
`uvicorn`), `worker` (Celery), `frontend`.

## Hosted (Render backend + Vercel frontend)

Streamlit Cloud does not apply here — this is a FastAPI + Next.js stack, not
a Streamlit app. Render (backend/Postgres/Redis/worker) + Vercel (Next.js
frontend) is the free-tier-friendly equivalent.

**Backend — Render, via `render.yaml` (Blueprint) at repo root:**

1. render.com → New → Blueprint → connect the `roykrishanu/pcrm` GitHub repo.
   It reads `render.yaml` and creates: `pcrm-backend` (web), `pcrm-worker`,
   `pcrm-redis`, `pcrm-db` (Postgres) automatically.
2. `SECRET_KEY` is auto-generated for the web service — for the worker,
   set it manually to the *same* value (Render dashboard → pcrm-worker →
   Environment) so both processes verify the same JWTs.
3. Edit `CORS_ORIGINS` and `FRONTEND_URL` env vars on `pcrm-backend` once you
   know your Vercel URL (step below) — they're placeholders in `render.yaml`.
4. Deploy. Confirm `https://pcrm-backend.onrender.com/health` returns `{"status":"ok"}`.

**Frontend — Vercel:**

1. vercel.com → New Project → import the same GitHub repo.
2. Set **Root Directory** to `frontend` (Vercel auto-detects Next.js from there).
3. Add env var `NEXT_PUBLIC_API_BASE_URL` = `https://pcrm-backend.onrender.com/api/v1`.
4. Deploy. Then go back to Render and set `CORS_ORIGINS`/`FRONTEND_URL` to
   the real `https://<project>.vercel.app` URL, and redeploy the backend —
   until that's set, login/register calls from the Vercel frontend will be
   blocked by CORS.

Render's free web service sleeps after inactivity (cold start delay on the
next request) and the free Postgres/Redis instances expire after 30/90 days
— fine for a demo, not for anything real. Upgrade the plan before real users.

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
