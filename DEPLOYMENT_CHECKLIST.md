# Deployment Checklist

Use this list before the first production cutover to **Vercel + Render + Neon**.  
Do **not** mark items complete until verified.

Reference: [docs/17_Deployment_Guide.md](./docs/17_Deployment_Guide.md) · [docs/18_Production_Deployment.md](./docs/18_Production_Deployment.md) · [PRODUCTION_ENV_CHECKLIST.md](./PRODUCTION_ENV_CHECKLIST.md)

---

## Backend ready

- [ ] `backend/requirements.txt` installs cleanly on Python 3.12
- [ ] `backend/runtime.txt` / `.python-version` pin Python 3.12
- [ ] `scripts/start.sh` listens on `$PORT`
- [ ] FastAPI lifespan validates production config and disposes DB on shutdown
- [ ] CORS configured for Vercel origin(s)
- [ ] GZip, security headers, rate-limit hook, request timing middleware present
- [ ] `/health`, `/liveness`, `/readiness`, `/metrics` reachable
- [ ] OpenTelemetry remains optional (`OTEL_ENABLED=false` unless collector exists)
- [ ] Production rejects weak JWT / default DB credentials / SQLite / `DEBUG=true`
- [ ] `render.yaml` present and secrets filled in Render dashboard

## Frontend ready

- [ ] `npm ci && npm run lint && npm run typecheck && npm test && npm run build` succeed
- [ ] `NEXT_PUBLIC_API_BASE_URL` (or `NEXT_PUBLIC_API_URL`) set to HTTPS API origin
- [ ] `NEXT_PUBLIC_ENVIRONMENT=production` set on Vercel
- [ ] Next.js security + static cache headers configured
- [ ] Vercel Root Directory = `frontend`
- [ ] Node 20+ engines satisfied
- [ ] API client attaches Bearer token from `localStorage.edp.access_token` when present

## Database ready

- [ ] Neon project created; SSL connection string available
- [ ] `DATABASE_URL` uses Neon host (app normalizes to `postgresql+psycopg` + `sslmode=require`)
- [ ] Consulting OLTP / analytics SQL applied (`analytics` schema/views)
- [ ] `alembic upgrade head` succeeds (baseline revision present)
- [ ] Pool settings appropriate for Neon plan
- [ ] `/readiness` returns 200 against Neon

## Environment variables ready

- [ ] Backend secrets set: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`
- [ ] Backend non-secrets: `APP_ENV=production`, `DEBUG=false`, SSL/startup flags
- [ ] Frontend public env set on Vercel (API URL, environment, flags)
- [ ] No secrets committed; `.env.example` templates reviewed

## Health endpoints verified

- [ ] `GET /health` → 200
- [ ] `GET /liveness` → 200
- [ ] `GET /readiness` → 200 (DB ok)
- [ ] `GET /metrics` → Prometheus text
- [ ] Frontend `GET /api/health` → 200

## Production build verified

- [ ] Backend image or Render build succeeds
- [ ] Frontend `next build` succeeds in CI and locally
- [ ] No turbopack required for production build

## Tests passing

- [ ] Backend `pytest` green
- [ ] Frontend Vitest green
- [ ] GitHub Actions CI green on target branch

## Security verified

- [ ] Strong JWT secret
- [ ] CORS allow-list (no wildcard in production)
- [ ] Auth required in production; dev-token disabled
- [ ] Docs UI disabled in production (`/docs`, `/redoc`)
- [ ] Security headers present
- [ ] Rate-limit hook in place (edge enforcement planned)

## Performance verified

- [ ] Compression enabled
- [ ] Cache-Control / ETag on analytics GET
- [ ] Response timing headers present
- [ ] Static assets long-cache on Vercel (`/_next/static`)

---

## Go / No-Go

| Gate | Status |
|------|--------|
| Backend ready | ☐ |
| Frontend ready | ☐ |
| Database ready | ☐ |
| Environment variables ready | ☐ |
| Health endpoints verified | ☐ |
| Production build verified | ☐ |
| Tests passing | ☐ |
| Security verified | ☐ |
| Performance verified | ☐ |

**Sign-off:** __________________  **Date:** __________
