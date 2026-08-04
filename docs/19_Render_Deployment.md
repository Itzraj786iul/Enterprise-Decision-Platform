# 19 — Render Backend Deployment

Guide for deploying the Enterprise Decision Platform **API** to [Render](https://render.com) from:

**GitHub:** [https://github.com/Itzraj786iul/Enterprise-Decision-Platform](https://github.com/Itzraj786iul/Enterprise-Decision-Platform)

This document **does not deploy** anything. It verifies Blueprint assets and provides a step-by-step operator checklist.

Related: [18 — Production Deployment](./18_Production_Deployment.md) · [PRODUCTION_ENV_CHECKLIST.md](../PRODUCTION_ENV_CHECKLIST.md) · [`render.yaml`](../render.yaml)

---

## 1. `render.yaml` verification

| Setting | Value in repo | Status |
|---------|---------------|--------|
| Service type | `web` (`edp-api`) | OK |
| Runtime | `python` | OK |
| Root directory | `backend` | OK |
| Branch | `main` | OK |
| Auto deploy | `true` | OK |
| Python version | `PYTHON_VERSION=3.12.8` (+ `backend/runtime.txt`) | OK |
| Build command | `pip install -r requirements.txt` | OK |
| Start command | `chmod +x scripts/start.sh && ./scripts/start.sh` | OK |
| Health check | `/readiness` | OK |
| Port | `$PORT` via `scripts/start.sh` (Render injects `PORT`) | OK |
| Host | `0.0.0.0` (`API_HOST`) | OK |
| Graceful shutdown | uvicorn `--timeout-graceful-shutdown 30` | OK |
| Secrets | `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` → `sync: false` | OK |

### Port configuration

Render sets `PORT` at runtime. `backend/scripts/start.sh` does:

```text
PORT="${PORT:-${API_PORT:-8000}}"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" ...
```

Do **not** hardcode port `8000` in the Render start command.

---

## 2. Environment variables (Render)

### Required

| Variable | Notes |
|----------|-------|
| `APP_ENV` | Must be `production` (Blueprint sets this) |
| `DEBUG` | Must be `false` |
| `DATABASE_URL` | Neon Postgres URL (set in dashboard — secret) |
| `JWT_SECRET_KEY` | ≥32 chars, not a placeholder (secret; alias `JWT_SECRET`) |
| `CORS_ORIGINS` | Exact frontend origin(s), comma-separated (set in dashboard) |

### Secret

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | Neon connection string; prefer `?sslmode=require` |
| `JWT_SECRET_KEY` | Signing secret for Bearer JWT |

> `CORS_ORIGINS` is not cryptographic, but Blueprint marks it `sync: false` so you must enter it manually (e.g. `https://your-app.vercel.app`).

### Optional (Blueprint pre-fills most)

| Variable | Recommended |
|----------|-------------|
| `ENVIRONMENT` | `production` (alias of `APP_ENV`) |
| `PYTHON_VERSION` | `3.12.8` |
| `LOG_LEVEL` | `INFO` |
| `LOG_JSON` | `true` |
| `API_HOST` | `0.0.0.0` |
| `DATABASE_SSL_REQUIRE` | `true` |
| `DATABASE_REQUIRED_ON_STARTUP` | `true` |
| `DATABASE_POOL_SIZE` | `5` |
| `DATABASE_MAX_OVERFLOW` | `5` |
| `DATABASE_POOL_RECYCLE` | `300` |
| `DATABASE_POOL_TIMEOUT` | `30` |
| `DATABASE_CONNECT_RETRIES` | `3` |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ISSUER` | `edp-api` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `GZIP_MINIMUM_SIZE` | `500` |
| `HTTP_CACHE_MAX_AGE_SECONDS` / `CACHE_CONTROL_MAX_AGE` | `30` |
| `SLOW_REQUEST_MS` | `1000` |
| `ANALYTICS_SCHEMA` | `analytics` |
| `ANALYTICS_VIEW_OVERRIDES` | empty unless remapping |
| `WEB_CONCURRENCY` | `1` |
| `OTEL_SERVICE_NAME` | `edp-api` |
| `OTEL_CONSOLE_EXPORT` | `false` |

### Feature flags

| Variable | Production expectation |
|----------|------------------------|
| `AUTH_REQUIRED` | `true` (forced when `APP_ENV=production`) |
| `AUTH_DEV_TOKEN_ENABLED` | `false` (forced off in production) |
| `METRICS_ENABLED` | `true` |
| `OTEL_ENABLED` | `false` until a collector exists |

`PORT` is injected by Render — do not set it manually unless debugging.

---

## 3. Exact deployment checklist

### Prerequisites (before Render)

- [ ] Neon database created  
- [ ] Analytics SQL applied (schema/views) — see docs/18  
- [ ] Strong `JWT_SECRET_KEY` generated (≥32 characters)  
- [ ] GitHub repo accessible: [Itzraj786iul/Enterprise-Decision-Platform](https://github.com/Itzraj786iul/Enterprise-Decision-Platform)  

### Render steps

1. [ ] **Create Render account** (https://dashboard.render.com)  
2. [ ] **Connect GitHub** — authorize the `Itzraj786iul/Enterprise-Decision-Platform` repository  
3. [ ] **New → Blueprint**  
4. [ ] **Select repository** `Enterprise-Decision-Platform` (branch `main`)  
5. [ ] **Verify `render.yaml` detection** — service `edp-api`, root `backend`, health `/readiness`  
6. [ ] **Configure environment variables** (secrets / required):  
   - [ ] `DATABASE_URL` = Neon URL  
   - [ ] `JWT_SECRET_KEY` = strong secret  
   - [ ] `CORS_ORIGINS` = frontend origin(s) (placeholder OK until Vercel exists)  
7. [ ] **Apply / start deployment**  
8. [ ] **Verify deployment logs** — build `pip install` succeeds; start shows `Starting EDP API on 0.0.0.0:<PORT>`  
9. [ ] **First-time DB migrate** (Render Shell from service):  
   ```bash
   alembic upgrade head
   ```  
10. [ ] **Verify endpoints** (replace host):  

```bash
curl -sS https://<service>.onrender.com/health
curl -sS https://<service>.onrender.com/readiness
curl -sS https://<service>.onrender.com/metrics | head
python scripts/check_deployment.py --base-url https://<service>.onrender.com
```

Pass criteria:

| Path | Expect |
|------|--------|
| `/health` | HTTP 200, `"status":"ok"`, version present |
| `/readiness` | HTTP 200 when DB is up |
| `/metrics` | Prometheus text containing `edp_` |

---

## 4. Expected URLs

After deploy, Render assigns a host like `edp-api-xxxx.onrender.com` (exact name may vary).

| Surface | URL pattern |
|---------|-------------|
| **Backend** | `https://<service>.onrender.com` |
| **Health** | `https://<service>.onrender.com/health` |
| **Readiness** | `https://<service>.onrender.com/readiness` |
| **Metrics** | `https://<service>.onrender.com/metrics` |
| **Platform features** | `https://<service>.onrender.com/api/v1/platform/features` |
| **OpenAPI /docs** | Disabled when `APP_ENV=production` |

Starters on free/sleeping plans may cold-start (30–60s) on first request.

---

## 5. Troubleshooting

### `ModuleNotFoundError`

- Confirm **Root Directory** is `backend` (Blueprint `rootDir`).  
- Confirm build ran: `pip install -r requirements.txt` from `backend/`.  
- Do not start from repo root (`app` package lives under `backend/app`).  

### Build timeout

- Retry deploy.  
- Keep `requirements.txt` lean (already production-only).  
- Avoid installing `requirements-dev.txt` on Render.  

### Missing requirements / dependency install failure

- Ensure `backend/requirements.txt` is present on `main`.  
- Pin Python `3.12.8` (`PYTHON_VERSION`).  
- Check logs for binary build errors (`psycopg[binary]` should work on Render Linux).  

### `DATABASE_URL` issues

- Use Neon connection string; app rewrites `postgresql://` → `postgresql+psycopg://`.  
- Rejected if still using `user:password@` defaults in production.  
- SQLite is not allowed when `APP_ENV=production`.  

### SSL issues

- Append `?sslmode=require` to Neon URL.  
- Keep `DATABASE_SSL_REQUIRE=true`.  
- Neon hosts auto-get `sslmode=require` via URL normalizer.  

### Port binding

- Must listen on `0.0.0.0:$PORT`.  
- Do not use `--port 8000` only.  
- Confirm start logs show the Render-assigned port.  

### Health check failures

- Render checks `/readiness`.  
- Failure usually means DB unreachable or SSL wrong.  
- Temporary: check `/health` (process) vs `/database` (DB detail).  
- Production forces `DATABASE_REQUIRED_ON_STARTUP=true` — service will not stay healthy without Neon.  

### Migration failures

```bash
# Render Shell
cd /opt/render/project/src   # or service working dir
alembic current
alembic upgrade head
```

- Baseline revision is `0001_baseline` (no-op).  
- Analytics views are **not** created by Alembic — apply consulting SQL to Neon separately.  
- If `alembic` not found: `pip install -r requirements.txt` then retry.  

### Weak JWT / config validation crash on boot

- `JWT_SECRET_KEY` must be ≥32 characters and not `change-me-in-production`.  
- `DEBUG` must be `false`.  

### CORS errors from browser

- Set `CORS_ORIGINS` to the exact Vercel origin (scheme + host, no trailing slash mismatch).  
- Redeploy after changing env vars.  

### Analytics routes return 401

- Expected in production (`AUTH_REQUIRED=true`).  
- Mint a JWT with the same `JWT_SECRET_KEY` and send `Authorization: Bearer …`.  
- Dev token endpoint is disabled in production.  

---

## 6. Post-deploy verification checklist

- [ ] Render service status = **Live**  
- [ ] Auto-Deploy enabled for `main`  
- [ ] `GET /health` → 200  
- [ ] `GET /readiness` → 200  
- [ ] `GET /metrics` → `edp_` series present  
- [ ] `GET /api/v1/platform/features` → 200  
- [ ] `alembic upgrade head` completed once  
- [ ] Neon connectivity confirmed  
- [ ] `CORS_ORIGINS` updated when frontend URL is known  
- [ ] `scripts/check_deployment.py --base-url https://<service>.onrender.com` passes  

---

## 7. Operator notes

- **Do not** commit real secrets.  
- **Do not** enable `AUTH_DEV_TOKEN_ENABLED` in production.  
- Prefer one web instance + `WEB_CONCURRENCY=1` on Neon free/launch tiers.  
- After Vercel is live, update `CORS_ORIGINS` and redeploy API.  
- Full platform sequence (Neon + Vercel + smoke): [docs/18_Production_Deployment.md](./18_Production_Deployment.md).  
