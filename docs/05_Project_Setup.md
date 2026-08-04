# Project Setup — Enterprise Decision Platform

Foundation scaffold documentation. This phase installs and runs the monorepo shell only — **no business logic, dashboards, analytics connections, Postgres usage, or ML APIs**.

## Prerequisites

- **Node.js** 20+
- **npm** 10+
- **Python** 3.10+ (3.12 recommended)
- **Docker Desktop** (optional, for compose)
- **Git**

## Installation

### 1. Clone / enter the monorepo

```bash
cd enterprise-decision-platform
```

### 2. Environment files

```bash
# Root reference (optional)
cp .env.example .env

# Frontend
cp frontend/.env.local.example frontend/.env.local

# Backend
cp backend/.env.example backend/.env
```

### 3. Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Backend dependencies

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements-dev.txt
cd ..
```

---

## Folder layout

```text
enterprise-decision-platform/
├── frontend/                 Next.js 15 App Router app
│   └── src/
│       ├── app/              Routes + API route handlers
│       ├── components/       Shared UI (ui, charts, layout, forms, …)
│       ├── features/         Domain feature modules (empty scaffolds)
│       ├── hooks/            Cross-cutting hooks
│       ├── lib/              Utilities
│       ├── services/         API clients
│       ├── store/            Zustand stores
│       ├── types/            TypeScript contracts
│       ├── styles/           Extra CSS tokens
│       └── config/           Public config
├── backend/
│   └── app/
│       ├── api/routes/       HTTP routers (placeholders)
│       ├── api/dependencies/ DI hooks (future auth/DB)
│       ├── core/             Settings & shared config
│       ├── database/         SQLAlchemy session (unwired)
│       ├── models/           ORM models (empty)
│       ├── schemas/          Pydantic schemas (empty)
│       ├── repositories/     Data access (empty)
│       ├── services/         Domain services (empty)
│       ├── analytics/        Analytics adapters (empty)
│       ├── ml/               ML adapters (empty)
│       ├── recommendations/  Recommendation engines (empty)
│       └── utils/            Helpers
├── shared/                   Cross-package contracts / constants
├── docs/                     Architecture & setup docs
├── scripts/                  Developer scripts
├── docker-compose.yml        Dev containers
└── .github/workflows/        CI (lint, build, tests)
```

### Frontend folder responsibilities

| Path | Role |
|------|------|
| `app/` | Next.js App Router pages and route handlers |
| `components/ui/` | Primitive shadcn/ui components |
| `components/charts/` | Shared chart wrappers |
| `components/dashboard/` | Shared dashboard chrome |
| `components/tables/` | Table primitives |
| `components/layout/` | Providers, shells, navigation |
| `components/forms/` | Form controls (RHF + Zod) |
| `components/feedback/` | Empty / loading / Coming Soon |
| `features/*/` | Domain modules composing the above |
| `hooks/` | Shared React hooks |
| `lib/` | Pure helpers (`cn`, etc.) |
| `services/` | HTTP / API transport |
| `store/` | Global Zustand state |
| `types/` | Shared TS types |
| `styles/` | Design tokens beyond `globals.css` |
| `config/` | Env-backed public configuration |
| `public/` | Static assets |

### Backend folder responsibilities

| Path | Role |
|------|------|
| `api/routes/` | Thin HTTP controllers |
| `api/dependencies/` | FastAPI dependencies |
| `core/` | Settings, security constants |
| `database/` | Engine / session / Base |
| `models/` | SQLAlchemy entities |
| `schemas/` | Pydantic I/O contracts |
| `repositories/` | Persistence abstractions |
| `services/` | Application services |
| `analytics/` | Analytics orchestration |
| `ml/` | Model inference adapters |
| `recommendations/` | Decision recommendation logic |
| `utils/` | Pure helpers |
| `tests/` | Pytest suite |
| `alembic/` | Schema migrations |

---

## Running the frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

| Route | Expected |
|-------|----------|
| `/` | Home — Coming Soon |
| `/dashboard` | Dashboard — Coming Soon |
| `/sales` | Sales — Coming Soon |
| `/customers` | Customers — Coming Soon |
| `/finance` | Finance — Coming Soon |
| `/operations` | Operations — Coming Soon |
| `/predictions` | Predictions — Coming Soon |
| `/recommendations` | Recommendations — Coming Soon |
| `/reports` | Reports — Coming Soon |
| `/settings` | Settings — Coming Soon |
| `/api/health` | `{ "status": "ok", "service": "frontend", ... }` |

Other scripts:

```bash
npm run lint
npm run typecheck
npm run build
npm run start
npm run format
```

---

## Running the backend

```bash
cd backend
# activate venv first
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

| Route | Expected |
|-------|----------|
| `GET /health` | `{ "status": "ok", "service": "backend", ... }` |
| `GET /dashboard` | Placeholder JSON |
| `GET /sales` | Placeholder JSON |
| `GET /customers` | Placeholder JSON |
| `GET /finance` | Placeholder JSON |
| `GET /operations` | Placeholder JSON |
| `GET /ml` | Placeholder JSON |
| `GET /recommendations` | Placeholder JSON |
| `GET /reports` | Placeholder JSON |

Quality:

```bash
ruff check .
pytest -q
```

> **Note:** `DATABASE_URL` is present in `.env` for future use. The foundation scaffold does **not** open a Postgres connection.

---

## Docker (development)

From the monorepo root:

```bash
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000/health](http://localhost:8000/health)

Stop:

```bash
docker compose down
```

Dockerfiles:

- `frontend/Dockerfile` — multi-stage (`deps` for compose/dev, `runner` for production-style image)
- `backend/Dockerfile` — slim Python image running Uvicorn

---

## Development workflow

1. **Branch** from `main` / `develop` for each feature.
2. **Scaffold only** in this phase — keep pages and routers as placeholders until the next implementation ticket.
3. **Frontend**: add domain code under `features/<domain>/`; keep `components/` reusable and dumb.
4. **Backend**: keep routers thin; put logic in `services/` → `repositories/` when you start implementing.
5. **Before PR**:
   - `npm run lint` + `npm run build` in `frontend/`
   - `ruff check .` + `pytest` in `backend/`
6. **CI** (`.github/workflows/ci.yml`) runs the same checks on push/PR.

### Suggested daily loop

```text
Pull → activate venvs → start backend → start frontend →
implement behind placeholders → lint/test → commit → push
```

Root convenience scripts (`package.json`):

```bash
npm run dev:frontend
npm run lint:frontend
npm run build:frontend
npm run docker:up
npm run docker:down
```

---

## Out of scope (this phase)

- Business KPI logic
- Dashboard UI
- Analytics SQL wiring
- PostgreSQL connections / Alembic migrations applied against a live DB
- ML model loading or inference APIs
- Authentication / authorization

These will be added in subsequent implementation phases on top of this foundation.
