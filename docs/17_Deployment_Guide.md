# 17 — Deployment Guide

Production deployment runbook for:

| Layer | Platform |
|-------|----------|
| Frontend | **Vercel** |
| Backend | **Render** |
| Database | **Neon** (PostgreSQL) |

This guide prepares the repository for deploy. It does **not** deploy anything.

Related: [16 — Production Readiness](./16_Production_Readiness.md), [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)

---

## Repository overview

```text
enterprise-decision-platform/
├── frontend/                 Next.js 15 (Vercel root directory)
├── backend/                  FastAPI (Render rootDir)
│   ├── scripts/start.sh      $PORT-aware uvicorn entrypoint
│   ├── runtime.txt           Python 3.12.8
│   └── alembic/              Migrations (baseline present)
├── render.yaml               Render Blueprint
├── docs/17_Deployment_Guide.md
└── DEPLOYMENT_CHECKLIST.md
```

Analytics SQL, OLTP DDL, and synthetic data generation live **in this repository** (`database/`, `sql/`, `data_generation/`). Neon must be seeded with those scripts — Alembic only tracks the API baseline.

---

## Deployment architecture

```text
Browser
  │
  ▼
Vercel (Next.js)  ──HTTPS──►  Render (FastAPI / uvicorn)
                                  │
                                  ▼
                              Neon PostgreSQL
                           (analytics schema + views)
```

- Frontend uses `NEXT_PUBLIC_API_BASE_URL` for browser `fetch` to the API.
- Backend CORS must list the Vercel production (and preview) origins.
- Metrics: `GET /metrics` on Render (restrict at the network edge if possible).
- Health: Render `healthCheckPath` = `/readiness`.

---

## Environment variables

### Backend (Render) — see `backend/.env.example`

| Variable | Required (prod) | Notes |
|----------|-----------------|-------|
| `APP_ENV` / `ENVIRONMENT` | yes | `production` |
| `DEBUG` | yes | `false` |
| `DATABASE_URL` | yes | Neon URL; SSL auto-applied |
| `DATABASE_SSL_REQUIRE` | recommended | `true` |
| `JWT_SECRET_KEY` / `JWT_SECRET` | yes | ≥32 chars, not a placeholder |
| `CORS_ORIGINS` | yes | `https://your-app.vercel.app` (+ custom domain) |
| `AUTH_REQUIRED` | forced true in prod | Bearer JWT required for analytics APIs |
| `OTEL_ENABLED` | no | leave `false` until collector exists |
| `HTTP_CACHE_MAX_AGE_SECONDS` / `CACHE_CONTROL_MAX_AGE` | no | default 30 |
| `METRICS_ENABLED` | no | default true |
| `PORT` | injected by Render | `start.sh` reads it |

### Frontend (Vercel) — see `frontend/.env.example`

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | yes | Public HTTPS API origin |
| `NEXT_PUBLIC_API_URL` | alias | Same as above |
| `NEXT_PUBLIC_ENVIRONMENT` | recommended | `production` |
| `NEXT_PUBLIC_APP_ENV` | alias | Same |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | no | UI feature flag |
| `NEXT_PUBLIC_AUTH_REQUIRED` | no | UI posture only; backend enforces |
| `NEXT_PUBLIC_DEV_ROLES` | non-prod only | Do not rely on for real IdP |

---

## Neon setup

1. Create a Neon project and database.
2. Copy the connection string.
3. Prefer: `postgresql://USER:PASSWORD@HOST/DB?sslmode=require`  
   The app rewrites to `postgresql+psycopg://` and ensures `sslmode=require` for Neon hosts / production.
4. Apply OLTP + analytics SQL from this repository (`database/`, `sql/analytical_views.sql`). Optionally load ML CSVs via `sql/load_ml_predictions.sql`.
5. Confirm schema `analytics` (or override with `ANALYTICS_SCHEMA`) exists.
6. Set Render `DATABASE_URL` to the Neon URL.
7. Keep pool sizes modest (`DATABASE_POOL_SIZE=5`, `DATABASE_MAX_OVERFLOW=5`) for Neon free/launch tiers.

---

## Migration commands

From `backend/`:

```bash
# Ensure DATABASE_URL points at Neon
export DATABASE_URL="postgresql://…?sslmode=require"

# Apply Alembic head (baseline no-op + future ORM revisions)
alembic upgrade head

# Show current revision
alembic current
```

**Note:** Business analytics views are **not** created by Alembic. Run the consulting SQL scripts against Neon before expecting dashboard/sales/finance data.

### Production startup sequence

1. Neon reachable + analytics views applied  
2. `alembic upgrade head`  
3. Render web service starts (`./scripts/start.sh`)  
4. Lifespan: config validation → DB ping (`DATABASE_REQUIRED_ON_STARTUP=true` in production) → ready  
5. Health check `/readiness` returns 200  
6. Vercel frontend points at Render URL  

---

## Render deployment

Blueprint: [`render.yaml`](../render.yaml)

### Option A — Blueprint

1. Connect the GitHub repo in Render.  
2. Apply Blueprint (`render.yaml`).  
3. Fill secrets: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`.  
4. Deploy.  
5. Open Shell → `alembic upgrade head` (first time).  

### Option B — Manual web service

| Setting | Value |
|---------|-------|
| Runtime | Python 3.12 |
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `chmod +x scripts/start.sh && ./scripts/start.sh` |
| Health check path | `/readiness` |
| Auto-deploy | On (`main`) |

Docker alternative: use `backend/Dockerfile` (also `$PORT`-aware via `scripts/start.sh`).

### Post-deploy smoke

```bash
curl -sS https://<api>/health
curl -sS https://<api>/readiness
curl -sS https://<api>/metrics | head
curl -sS https://<api>/api/v1/platform/features
```

With `APP_ENV=production`, analytics routes require `Authorization: Bearer <jwt>`. Mint tokens offline with the same `JWT_SECRET_KEY` (IdP not connected yet), or store a token in the browser as `localStorage.edp.access_token` (the API client attaches it automatically).

---

## Vercel deployment

### Why there is no `vercel.json`

Default Vercel Next.js detection is preferred:

- Framework preset handles install/build/output  
- Security and static cache headers are already in `frontend/next.config.ts`  
- `output: "standalone"` is for Docker and is safely ignored by Vercel  
- Avoiding `vercel.json` reduces config drift  

Set **Root Directory** = `frontend` in the Vercel project.

### Steps

1. Import GitHub repo → Root Directory `frontend` → Node 20.  
2. Env vars from `frontend/.env.example` (production values).  
3. Deploy.  
4. Copy the Vercel URL into Render `CORS_ORIGINS` (include preview origins if needed).  
5. Redeploy API if CORS changed.  

### Build / runtime

| Command | Value |
|---------|-------|
| Install | `npm ci` (Vercel default) |
| Build | `npm run build` → `next build` |
| Start | Vercel managed (`next start` equivalent) |

---

## Security checklist

- Strong `JWT_SECRET_KEY` (≥32 chars)  
- `DEBUG=false`, `APP_ENV=production`  
- CORS locked to known Vercel origins (no `*`)  
- Dev token endpoint disabled in production  
- `/docs` and `/redoc` disabled when `APP_ENV=production`  
- Security headers middleware + Next headers  
- Rate-limit **hook** present (edge/gateway should enforce real limits)  
- Cookie auth not used yet — headers document future `Secure; HttpOnly; SameSite` posture  
- Never commit `.env` secrets  

---

## Performance checklist

- GZip middleware enabled  
- Cache-Control + weak ETag on analytics GET responses  
- `X-Response-Time-Ms` / `X-Request-ID`  
- Next.js immutable cache for `/_next/static`  
- Connection pooling + `pool_pre_ping` for Neon  

---

## CI/CD

GitHub Actions: `.github/workflows/ci.yml`

| Job | Checks |
|-----|--------|
| Frontend | lint, typecheck, vitest, production `next build` |
| Backend | ruff, pytest |

Push to `main` / `master` / `develop` or open a PR to run CI. Render/Vercel auto-deploy from Git once connected.

---

## Rollback strategy

1. **Vercel:** Promote previous Deployment in the dashboard Instant Rollback.  
2. **Render:** Redeploy the prior successful deploy from Events / history.  
3. **Database:** Alembic baseline is no-op; reverse only future revisions with `alembic downgrade -1`. Never drop Neon analytics views without a backup.  
4. **Config:** Keep previous env var values documented; revert secrets only via platform dashboards.  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Render health failing | DB down / SSL missing | Check Neon, `sslmode=require`, `/readiness` body |
| CORS errors in browser | Origin not in `CORS_ORIGINS` | Add exact Vercel URL (scheme + host) |
| 401 on all `/api/v1/*` | Production auth forced | Attach Bearer JWT (`localStorage.edp.access_token`) |
| Empty analytics | Views missing on Neon | Apply consulting SQL scripts |
| Frontend calls localhost | Missing Vercel env | Set `NEXT_PUBLIC_API_BASE_URL` and redeploy |
| Pool exhaustion | Too many workers/instances | Lower `DATABASE_POOL_*`, `WEB_CONCURRENCY=1` |
| Alembic “no such revision” | Old empty tree | Ensure `0001_baseline` is present; `alembic upgrade head` |

---

## Production checklist

Use [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) before the first go-live.
