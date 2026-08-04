# Production Environment Variables Checklist

Fill values in Render / Vercel dashboards. Never commit secrets.

See also: [docs/18_Production_Deployment.md](./docs/18_Production_Deployment.md)

---

## Backend (Render) — Required

| Variable | Example / notes | Set |
|----------|-----------------|-----|
| `APP_ENV` | `production` | ☐ |
| `DEBUG` | `false` | ☐ |
| `DATABASE_URL` | Neon URL with SSL | ☐ |
| `JWT_SECRET_KEY` | ≥32 char random secret | ☐ |
| `CORS_ORIGINS` | `https://<app>.vercel.app` (+ custom domain) | ☐ |

## Backend — Secrets

| Variable | Notes | Set |
|----------|-------|-----|
| `DATABASE_URL` | Neon connection string (secret) | ☐ |
| `JWT_SECRET_KEY` (alias `JWT_SECRET`) | Signing key (secret) | ☐ |

> `CORS_ORIGINS` is not a cryptographic secret but must be set per environment and should not use `*`.

## Backend — Optional

| Variable | Default / recommendation | Set |
|----------|--------------------------|-----|
| `ENVIRONMENT` | alias of `APP_ENV` | ☐ |
| `LOG_LEVEL` | `INFO` | ☐ |
| `LOG_JSON` | `true` (forced in prod) | ☐ |
| `DATABASE_SSL_REQUIRE` | `true` | ☐ |
| `DATABASE_REQUIRED_ON_STARTUP` | `true` (forced in prod) | ☐ |
| `DATABASE_POOL_SIZE` | `5` | ☐ |
| `DATABASE_MAX_OVERFLOW` | `5` | ☐ |
| `DATABASE_POOL_RECYCLE` | `300` (Neon-friendly) | ☐ |
| `JWT_ALGORITHM` | `HS256` | ☐ |
| `JWT_ISSUER` | `edp-api` | ☐ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | ☐ |
| `AUTH_REQUIRED` | forced `true` in production | ☐ |
| `AUTH_DEV_TOKEN_ENABLED` | forced `false` in production | ☐ |
| `METRICS_ENABLED` | `true` | ☐ |
| `OTEL_ENABLED` | `false` until collector exists | ☐ |
| `OTEL_SERVICE_NAME` | `edp-api` | ☐ |
| `OTEL_CONSOLE_EXPORT` | `false` | ☐ |
| `GZIP_MINIMUM_SIZE` | `500` | ☐ |
| `HTTP_CACHE_MAX_AGE_SECONDS` / `CACHE_CONTROL_MAX_AGE` | `30` | ☐ |
| `SLOW_REQUEST_MS` | `1000` | ☐ |
| `ANALYTICS_SCHEMA` | `analytics` | ☐ |
| `ANALYTICS_VIEW_OVERRIDES` | empty unless remapping views | ☐ |
| `WEB_CONCURRENCY` | `1` | ☐ |
| `PYTHON_VERSION` | `3.12.8` (Render) | ☐ |

## Backend — Feature flags

| Variable | Role | Set |
|----------|------|-----|
| `AUTH_REQUIRED` | Enforce JWT on analytics APIs (prod forced on) | ☐ |
| `METRICS_ENABLED` | Expose `/metrics` | ☐ |
| `OTEL_ENABLED` | OpenTelemetry tracing | ☐ |
| `AUTH_DEV_TOKEN_ENABLED` | Dev JWT mint (must stay off in prod) | ☐ |

---

## Frontend (Vercel) — Required

| Variable | Example / notes | Set |
|----------|-----------------|-----|
| `NEXT_PUBLIC_API_BASE_URL` | `https://edp-api.onrender.com` | ☐ |

## Frontend — Optional / aliases

| Variable | Notes | Set |
|----------|-------|-----|
| `NEXT_PUBLIC_API_URL` | alias of API base URL | ☐ |
| `NEXT_PUBLIC_ENVIRONMENT` | `production` | ☐ |
| `NEXT_PUBLIC_APP_ENV` | alias of environment | ☐ |
| `NEXT_PUBLIC_APP_NAME` | display name | ☐ |

## Frontend — Feature flags

| Variable | Notes | Set |
|----------|-------|-----|
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | UI analytics flag (`true`/`false`) | ☐ |
| `NEXT_PUBLIC_AUTH_REQUIRED` | UI posture only; backend enforces auth | ☐ |
| `NEXT_PUBLIC_DEV_ROLES` | **non-prod only** demo RBAC | ☐ |

## Frontend — Secrets

None. Never put JWT secrets or database URLs in `NEXT_PUBLIC_*` variables.

---

## Sign-off

| Gate | Owner | Date |
|------|-------|------|
| Backend env complete | | |
| Frontend env complete | | |
| Secrets rotated / stored in platform vaults | | |
