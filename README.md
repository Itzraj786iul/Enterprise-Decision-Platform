# Enterprise Decision Platform

Production-ready monorepo for the Enterprise Decision Intelligence Platform  
(**Vercel** frontend · **Render** backend · **Neon** PostgreSQL).

## Stack

| Layer | Technologies |
|-------|----------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, Recharts, React Hook Form, Zod, Lucide |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL / Neon |
| Deploy | Vercel + Render Blueprint (`render.yaml`) |

## Structure

```text
enterprise-decision-platform/
├── frontend/                 Next.js (Vercel Root Directory)
├── backend/                  FastAPI (Render rootDir)
├── shared/                   Cross-cutting contracts
├── docs/                     Architecture + deployment docs
├── scripts/                  Smoke + deployment verification
├── render.yaml               Render Blueprint
├── DEPLOYMENT_CHECKLIST.md
├── PRODUCTION_ENV_CHECKLIST.md
├── docker-compose.yml        Local development
└── .github/workflows         CI (lint, test, build)
```

## License

No root `LICENSE` is committed yet. **Recommendation for public repos: MIT** — confirm ownership / client IP before adding.

## Quick start

See **[docs/05_Project_Setup.md](docs/05_Project_Setup.md)** for full installation and workflow details.

```bash
# Frontend
cd frontend
cp .env.local.example .env.local
npm install
npm run dev

# Backend (separate terminal)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Health checks

- Frontend: `GET /api/health`
- Backend: `GET /health`

## Design system

Reusable UI foundation (no dashboard pages): see **[docs/06_Design_System.md](docs/06_Design_System.md)**.

## Application shell

Enterprise SaaS chrome (sidebar, top nav, command palette, search): see **[docs/07_Application_Shell.md](docs/07_Application_Shell.md)**.

## Backend foundation

FastAPI infrastructure (DB lifecycle, DI, repos, health): see **[docs/08_Backend_Foundation.md](docs/08_Backend_Foundation.md)**.

## Analytics service layer

Read-only analytics view access (repos/services/DTOs): see **[docs/09_Analytics_Service_Layer.md](docs/09_Analytics_Service_Layer.md)**.

## Executive dashboard

First vertical slice (API + UI): see **[docs/10_Executive_Dashboard.md](docs/10_Executive_Dashboard.md)**.

## Analytics UI framework

Reusable analytics page infrastructure (layout, filters, charts, hooks — no feature pages): see **[docs/11_Analytics_UI_Framework.md](docs/11_Analytics_UI_Framework.md)**.

## Sales intelligence

Commercial analytics vertical slice (API + UI on the Analytics Framework): see **[docs/12_Sales_Intelligence.md](docs/12_Sales_Intelligence.md)**.

## Customer intelligence

Customer lifecycle / RFM / cohort / churn vertical slice: see **[docs/13_Customer_Intelligence.md](docs/13_Customer_Intelligence.md)**.

## Operations intelligence

Inventory, supplier, returns, and warehouse vertical slice: see **[docs/14_Operations_Intelligence.md](docs/14_Operations_Intelligence.md)**.

## Finance intelligence

Profitability, costs, cashflow, and budget vertical slice: see **[docs/15_Finance_Intelligence.md](docs/15_Finance_Intelligence.md)**.

## Production readiness

Auth/RBAC, feature registry, OpenAPI, metrics, tracing prep, and performance headers: see **[docs/16_Production_Readiness.md](docs/16_Production_Readiness.md)**.

## Deployment (Vercel + Render + Neon)

| Doc | Purpose |
|-----|---------|
| **[docs/17_Deployment_Guide.md](docs/17_Deployment_Guide.md)** | Architecture, env templates, first-time setup |
| **[docs/18_Production_Deployment.md](docs/18_Production_Deployment.md)** | Full production sequence, smoke tests, rollback, monitoring |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Go / no-go checklist |
| **[PRODUCTION_ENV_CHECKLIST.md](PRODUCTION_ENV_CHECKLIST.md)** | Required / optional / secrets / feature flags |

Render Blueprint: [`render.yaml`](render.yaml). Vercel: Root Directory = `frontend` (no `vercel.json` required).

Post-deploy verification:

```bash
python scripts/check_deployment.py --base-url https://<api>.onrender.com
python scripts/check_deployment.py --base-url https://<api>.onrender.com --token "$JWT"
```

Platform endpoints: `GET /metrics`, `GET /api/v1/platform/features`, `GET /api/v1/auth/me`, `POST /api/v1/auth/dev-token` (non-prod).

## Routes

| Frontend | Backend | Status |
|----------|---------|--------|
| `/` | `/health` | Live |
| `/dashboard` | `/api/v1/dashboard/*` | Live |
| `/sales` | `/api/v1/sales/*` | Live |
| `/customers` | `/api/v1/customers/*` | Live |
| `/operations` | `/api/v1/operations/*` | Live |
| `/finance` | `/api/v1/finance/*` | Live |
| `/predictions` | `/ml` | Coming soon |
| `/recommendations` | `/recommendations` | Coming soon |
| `/reports` | `/reports` | Coming soon |
| `/settings` | — | Live (shell) |
| — | `/metrics` | Live |
| — | `/api/v1/platform/features` | Live |
