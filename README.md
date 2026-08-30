# Real Estate Lead CRM

Multi-tenant SaaS CRM for real-estate agents, agencies, brokers, and builders:
lead capture/scoring, property management + matching, visits, deals,
communication, automation, and reporting.

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for what's built, what isn't, and
the exact next task. See `docs/` for architecture, API, security, database,
deployment, and testing details.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.x (async), Alembic, PostgreSQL, Redis, Celery
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Auth**: JWT access tokens + rotating opaque refresh tokens, RBAC with per-organization roles

## Local development (without Docker)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
cp ../.env.example ../.env   # then edit SECRET_KEY at minimum
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Local development (with Docker)

```bash
cp .env.example .env   # edit SECRET_KEY at minimum
docker compose up --build
```

Backend: http://localhost:8000/docs · Frontend: http://localhost:3000

## Tests

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m ruff check app tests
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/API.md`](docs/API.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/DATABASE.md`](docs/DATABASE.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/TESTING.md`](docs/TESTING.md)
