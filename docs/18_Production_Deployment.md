# 18 — Production Deployment

Complete production deployment sequence for **Vercel (frontend) + Render (backend) + Neon (PostgreSQL)**.

This document prepares the team to deploy. It does **not** connect cloud accounts or perform the deploy.

Related:

- [17 — Deployment Guide](./17_Deployment_Guide.md)
- [16 — Production Readiness](./16_Production_Readiness.md)
- [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)
- [PRODUCTION_ENV_CHECKLIST.md](../PRODUCTION_ENV_CHECKLIST.md)
- [`scripts/check_deployment.py`](../scripts/check_deployment.py)

---

## Cloud architecture

```text
                     ┌──────────────────────┐
   Users ──────────► │  Vercel (Next.js)    │
                     │  frontend/           │
                     └──────────┬───────────┘
                                │ HTTPS
                                │ NEXT_PUBLIC_API_BASE_URL
                                ▼
                     ┌──────────────────────┐
                     │  Render (FastAPI)    │
                     │  backend/ + start.sh │
                     │  /readiness health   │
                     └──────────┬───────────┘
                                │ SSL (sslmode=require)
                                ▼
                     ┌──────────────────────┐
                     │  Neon PostgreSQL     │
                     │  OLTP + analytics.*  │
                     └──────────────────────┘
```

| Layer | Platform | Root / artifact |
|-------|----------|-----------------|
| Frontend | Vercel | `frontend/` (Root Directory) |
| Backend | Render | `backend/` (`render.yaml` Blueprint) |
| Database | Neon | External SQL + Alembic baseline |

---

## GitHub repository preparation

### Release-ready root structure

```text
enterprise-decision-platform/
├── .github/workflows/ci.yml
├── .gitignore
├── README.md
├── DEPLOYMENT_CHECKLIST.md
├── PRODUCTION_ENV_CHECKLIST.md
├── render.yaml
├── docs/18_Production_Deployment.md
├── scripts/check_deployment.py
├── frontend/                 # Vercel
└── backend/                  # Render
```

### `.gitignore`

Root `.gitignore` excludes secrets (`.env`, `.env.local`), virtualenvs, `node_modules`, Next.js build output, caches, and OS junk. Ensure `.vercel/` remains ignored locally after linking a project.

### LICENSE

No root `LICENSE` file is present. **Recommendation:** add an **MIT** license before making the repository public, after confirming ownership/client IP rules. Do not add a license automatically without stakeholder approval.

### Manual GitHub steps (required before cloud Git deploy)

```bash
cd enterprise-decision-platform
git init
git add .
git commit -m "chore: release-ready Enterprise Decision Platform"
# Create empty GitHub repo, then:
git branch -M main
git remote add origin git@github.com:<org>/<repo>.git
git push -u origin main
```

CI (`.github/workflows/ci.yml`) runs on push/PR to `main` / `master` / `develop`.

---

## Complete deployment sequence

### 0. Prerequisites

- GitHub repo pushed
- Neon, Render, and Vercel accounts available (you connect them manually)
- Strong JWT secret generated (≥32 characters)
- Analytics SQL available from the parent consulting repo

### 1. Create Neon database

1. Neon Console → New Project → create database.
2. Copy the connection string.
3. Prefer including SSL: `?sslmode=require`.
4. The API rewrites `postgresql://` → `postgresql+psycopg://` and ensures SSL for Neon / production.

### 2. Run Alembic migrations

From a machine (or Render Shell) with `DATABASE_URL` set:

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
alembic upgrade head
alembic current
```

Expected: revision `0001_baseline` (no-op platform baseline). Business tables/views are **not** created here.

### 3. Apply analytics SQL views

Against the same Neon database, apply consulting SQL **in order**:

```bash
# From parent consulting repository (paths relative to that repo)
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/indexes.sql
psql "$DATABASE_URL" -f database/views.sql
psql "$DATABASE_URL" -f sql/analytical_views.sql
psql "$DATABASE_URL" -f sql/stored_procedures.sql   # optional helpers
```

Load data as required by your data pipeline (`data_generation/` or warehouse loads).

### 4. Verify analytics objects

```sql
-- Schema present
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'analytics';

-- Sample view inventory (names depend on analytical_views.sql)
SELECT table_schema, table_name
FROM information_schema.views
WHERE table_schema = 'analytics'
ORDER BY 1, 2
LIMIT 50;
```

Confirm `ANALYTICS_SCHEMA` (default `analytics`) matches Neon.

### 5. Deploy backend on Render

1. Render → New → Blueprint → select repo → apply `render.yaml`.
2. Set secrets: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` (temporary placeholder OK until Vercel URL exists).
3. Confirm:
   - Python: `PYTHON_VERSION=3.12.8`
   - Build: `pip install -r requirements.txt`
   - Start: `chmod +x scripts/start.sh && ./scripts/start.sh`
   - Health: `/readiness`
   - Auto Deploy: `true` on `main`
4. Deploy and wait for healthy service.
5. Graceful shutdown: `start.sh` uses uvicorn `--timeout-graceful-shutdown 30` and lifespan disposes the DB pool.

### 6. Deploy frontend on Vercel

1. Import GitHub repo.
2. **Root Directory:** `frontend`
3. Framework: Next.js (default). **No `vercel.json` required** — headers/cache live in `next.config.ts`.
4. Set env:
   - `NEXT_PUBLIC_API_BASE_URL=https://<render-service>.onrender.com`
   - `NEXT_PUBLIC_ENVIRONMENT=production`
5. Deploy.
6. Copy the Vercel URL into Render `CORS_ORIGINS` (include custom domain / preview origins as needed) and redeploy API if CORS changed.

### 7. Run health checks

```bash
# Automated
python scripts/check_deployment.py --base-url https://<api>.onrender.com
python scripts/check_deployment.py --base-url https://<api>.onrender.com --token "$JWT"

# Manual
curl -sS https://<api>.onrender.com/health
curl -sS https://<api>.onrender.com/readiness
curl -sS https://<api>.onrender.com/database
curl -sS https://<api>.onrender.com/metrics | head
curl -sS https://<frontend>.vercel.app/api/health
```

### 8. Smoke tests (manual)

See [Smoke tests](#smoke-tests) below.

---

## Render review (`render.yaml`)

| Setting | Value | Status |
|---------|-------|--------|
| Python version | `3.12.8` via `PYTHON_VERSION` | OK |
| Build command | `pip install -r requirements.txt` | OK |
| Start command | `./scripts/start.sh` (`$PORT`) | OK |
| Health endpoint | `/readiness` | OK |
| Auto Deploy | `true` / branch `main` | OK |
| Env vars | non-secrets in Blueprint; secrets `sync: false` | OK |
| Graceful shutdown | uvicorn 30s + DB dispose | OK |
| Root directory | `backend` | OK |

---

## Vercel review

| Setting | Value | Status |
|---------|-------|--------|
| Root Directory | `frontend` | Configure in dashboard |
| Build | `npm run build` → `next build` | OK |
| Output | Next default on Vercel; `standalone` for Docker only | OK |
| API URL | `NEXT_PUBLIC_API_BASE_URL` (+ alias `NEXT_PUBLIC_API_URL`) | OK |
| Static assets | `/_next/static` immutable cache headers | OK |
| Security headers | `next.config.ts` | OK |
| `vercel.json` | **Not used** — defaults preferred | OK |

---

## Environment variables

Use [PRODUCTION_ENV_CHECKLIST.md](../PRODUCTION_ENV_CHECKLIST.md) for the signed checklist.

Summary:

| Class | Backend | Frontend |
|-------|---------|----------|
| **Required** | `APP_ENV`, `DEBUG`, `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` | `NEXT_PUBLIC_API_BASE_URL` |
| **Secrets** | `DATABASE_URL`, `JWT_SECRET_KEY` | none |
| **Optional** | pools, OTEL, cache TTLs, analytics schema | env aliases, app name |
| **Feature flags** | `AUTH_REQUIRED`, `METRICS_ENABLED`, `OTEL_ENABLED` | `NEXT_PUBLIC_ENABLE_ANALYTICS`, `NEXT_PUBLIC_AUTH_REQUIRED` |

---

## Deployment verification script

```bash
python scripts/check_deployment.py --base-url https://<api>.onrender.com
python scripts/check_deployment.py --base-url https://<api>.onrender.com --token "<jwt>"
```

Checks:

- Health / readiness / database
- Metrics (`edp_` series)
- Platform features API
- Auth `/api/v1/auth/me`
- Optional dashboard overview with JWT
- Response headers (`X-Request-ID`, `X-Response-Time-Ms`, security headers)
- Version from `/health`
- OpenAPI probe (404 acceptable in production)

---

## Smoke tests

Perform after automated checks pass. Production forces JWT — store a token in `localStorage.edp.access_token` or send `Authorization: Bearer …`.

| Area | Steps | Pass criteria |
|------|-------|---------------|
| **Executive Dashboard** | Open `/dashboard` | KPIs/sections load or show empty/unavailable states without hard crash |
| **Sales** | Open `/sales` | Page renders; filters work; API not 5xx |
| **Customer** | Open `/customers` | Page renders |
| **Operations** | Open `/operations` | Page renders |
| **Finance** | Open `/finance` | Page renders |
| **Authentication** | Call `/api/v1/auth/me` with/without token | Anonymous vs authenticated identity correct |
| **RBAC** | Token with `finance` role hits `/api/v1/sales/overview` | `403`; finance routes allowed |
| **Metrics** | `GET /metrics` | Prometheus text includes `edp_http_requests_total` |
| **OpenAPI** | `GET /docs` / `/openapi.json` | Disabled/404 in production; available in non-prod |

API quick probes (with token):

```bash
curl -H "Authorization: Bearer $JWT" https://<api>/api/v1/dashboard/overview
curl -H "Authorization: Bearer $JWT" https://<api>/api/v1/sales/overview
curl -H "Authorization: Bearer $JWT" https://<api>/api/v1/customers/overview
curl -H "Authorization: Bearer $JWT" https://<api>/api/v1/operations/overview
curl -H "Authorization: Bearer $JWT" https://<api>/api/v1/finance/overview
```

---

## Rollback strategy

| Layer | Action |
|-------|--------|
| **Vercel** | Deployments → prior production → **Promote** / Instant Rollback |
| **Render** | Events → previous successful deploy → **Redeploy** |
| **Config** | Revert env vars in dashboards to last known-good; redeploy |
| **Alembic** | Baseline is no-op; for future revisions use `alembic downgrade -1` only with a backup |
| **Neon** | Point-in-time restore / branch restore from Neon console; never drop `analytics` views without backup |
| **DNS** | If custom domains used, keep previous DNS until new stack verified |

Rollback decision tree:

1. UI-only regression → roll back Vercel only  
2. API regression → roll back Render; keep Neon  
3. Data/schema regression → restore Neon first, then redeploy API  

---

## Monitoring

| Signal | Where |
|--------|-------|
| API logs | Render → Service → Logs (JSON when `LOG_JSON=true`) |
| Frontend logs | Vercel → Project → Logs / Analytics |
| Database | Neon Console → Monitoring (connections, storage, compute) |
| Liveness | `GET /health`, `GET /liveness` |
| Readiness | `GET /readiness` (Render health check) |
| DB probe | `GET /database` |
| Metrics | `GET /metrics` (scrape with Prometheus/Grafana if desired) |
| Slow requests | Render logs: `slow request` warnings + `edp_http_slow_requests_total` |
| Auth failures | `edp_auth_failures_total` |

Recommended alerts (configure manually):

- Render health check failing  
- `/readiness` ≠ 200 for >2 minutes  
- Neon connection saturation  
- 5xx rate spike on `edp_http_errors_total`  

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Render deploy unhealthy | DB SSL / wrong URL | Fix Neon URL + `sslmode=require` |
| Browser CORS errors | Origin missing | Update `CORS_ORIGINS`, redeploy API |
| All analytics 401 | Prod auth on, no JWT | Mint JWT with same secret; set `localStorage.edp.access_token` |
| Empty charts | Views/data missing | Re-run analytics SQL + data load |
| Frontend hits localhost | Env missing at build | Set `NEXT_PUBLIC_API_BASE_URL`, redeploy Vercel |
| `/docs` 404 | Expected in production | Use non-prod or `/openapi.json` if enabled |
| Pool errors | Too many connections | Lower pool / `WEB_CONCURRENCY` |

---

## Expected public URLs (after deploy)

Replace placeholders with your project names:

| Surface | URL pattern |
|---------|-------------|
| **Frontend** | `https://<project>.vercel.app` |
| **Backend** | `https://<service>.onrender.com` |
| **Health** | `https://<service>.onrender.com/health` |
| **Readiness** | `https://<service>.onrender.com/readiness` |
| **Metrics** | `https://<service>.onrender.com/metrics` |
| **OpenAPI** | Development only: `https://<service>.onrender.com/docs` (disabled when `APP_ENV=production`) |

---

## Estimated timeline

| Phase | Estimate |
|-------|----------|
| GitHub push + CI green | 15–30 min |
| Neon create + SQL apply | 30–60 min |
| Render first deploy + secrets | 20–40 min |
| Vercel deploy + CORS update | 15–30 min |
| Verification + smoke | 30–45 min |
| **Total** | **≈ 2–4 hours** (first production cutover) |
