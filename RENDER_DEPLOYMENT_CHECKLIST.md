# Render Deployment Checklist

Repo: [https://github.com/Itzraj786iul/Enterprise-Decision-Platform](https://github.com/Itzraj786iul/Enterprise-Decision-Platform)

Guide: [docs/19_Render_Deployment.md](./docs/19_Render_Deployment.md)

**Do not deploy from this checklist automatically — execute steps in the Render dashboard.**

---

## A. `render.yaml` verified

- [x] Build: `pip install -r requirements.txt`
- [x] Start: `./scripts/start.sh` (uses `$PORT`)
- [x] Health: `/readiness`
- [x] Root: `backend`
- [x] Python: `3.12.8`
- [x] Auto deploy: `true` on `main`
- [x] Secrets: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` (`sync: false`)

## B. Prerequisites

- [ ] Neon database ready
- [ ] Analytics SQL applied (if you need live analytics data)
- [ ] JWT secret generated (≥32 chars)
- [ ] GitHub repo connected to Render

## C. Deploy steps

1. [ ] Create Render account
2. [ ] Connect GitHub repository
3. [ ] Select **Blueprint** deployment
4. [ ] Select `Enterprise-Decision-Platform`
5. [ ] Verify `render.yaml` detection (`edp-api`)
6. [ ] Configure env vars:
   - [ ] `DATABASE_URL` (**Secret / Required**)
   - [ ] `JWT_SECRET_KEY` (**Secret / Required**)
   - [ ] `CORS_ORIGINS` (**Required** — set manually)
7. [ ] Start deployment
8. [ ] Verify build/start logs
9. [ ] Run `alembic upgrade head` in Render Shell
10. [ ] Verify:
    - [ ] `/health`
    - [ ] `/readiness`
    - [ ] `/metrics`

## D. Environment classification (quick)

| Variable | Class |
|----------|-------|
| `APP_ENV`, `DEBUG` | Required |
| `DATABASE_URL` | Required + Secret |
| `JWT_SECRET_KEY` | Required + Secret |
| `CORS_ORIGINS` | Required (manual) |
| `METRICS_ENABLED`, `OTEL_ENABLED`, `AUTH_REQUIRED`, `AUTH_DEV_TOKEN_ENABLED` | Feature flags |
| Pool / cache / log / JWT algorithm settings | Optional |

## E. Expected URLs

| Surface | Pattern |
|---------|---------|
| Backend | `https://<service>.onrender.com` |
| Health | `https://<service>.onrender.com/health` |
| Readiness | `https://<service>.onrender.com/readiness` |
| Metrics | `https://<service>.onrender.com/metrics` |

## F. Sign-off

| Gate | Done |
|------|------|
| Service Live | ☐ |
| Health 200 | ☐ |
| Readiness 200 | ☐ |
| Metrics OK | ☐ |
| Migrations applied | ☐ |

**Operator:** ____________  **Date:** ____________
