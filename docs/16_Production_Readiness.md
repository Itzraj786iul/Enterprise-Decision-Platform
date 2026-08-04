# 16 — Production Readiness

Platform capabilities for security, observability, and operational readiness.  
**No analytics calculations, dashboard layouts, or feature behavior were changed.** Existing APIs remain backward compatible when `AUTH_REQUIRED=false` (default outside production).

---

## Security architecture

### Authentication

| Piece | Location | Notes |
|-------|----------|-------|
| JWT encode/decode | `backend/app/auth/jwt.py` | HS256 local tokens; issuer claim validated |
| OAuth-ready interface | `backend/app/auth/oauth.py` | `OAuthProvider` protocol + `UnconfiguredOAuthProvider` stub — **no IdP connected** |
| User principal | `backend/app/auth/models.py` | `AuthenticatedUser` with roles + permissions |
| Dev token mint | `POST /api/v1/auth/dev-token` | Disabled in production |
| Current user | `GET /api/v1/auth/me` | Anonymous when no Bearer token |

Bearer JWT is accepted via `Authorization: Bearer <token>`. Claims expected: `sub`, `roles[]`, `exp`, optional `email`.

### Authorization (RBAC)

Roles: **Admin**, **Executive**, **Finance**, **Operations**, **Sales**, **Analyst**, **Viewer**.

Permissions are string capabilities (`sales:read`, `finance:read`, `export:run`, `admin:all`, …). Role → permission maps live in `ROLE_PERMISSIONS`.

**Permission middleware** (`RequestContextMiddleware`) resolves the feature for the request path from the feature registry and enforces required permissions **without modifying route handlers**.

| Mode | Behavior |
|------|----------|
| `AUTH_REQUIRED=false` | Anonymous access allowed (compat). If a JWT is present, its permissions are still enforced. |
| `AUTH_REQUIRED=true` | Production default. Protected `/api/v1/*` analytics routes require a valid JWT with matching permissions. |
| Public paths | `/health`, `/liveness`, `/readiness`, `/metrics`, OpenAPI docs, `/api/v1/platform/*`, `/api/v1/auth/*` |

Handler-level checks remain available via `require_permissions(...)` dependency when needed later.

---

## Feature registry

Central catalog of every analytics module (backend + frontend mirrors):

| Field | Purpose |
|-------|---------|
| Route | UI path |
| Navigation label / icon | Shell navigation |
| Permissions | RBAC gate |
| Supported filters | Declared filter vocabulary |
| Export support | Whether exports are in scope |
| Availability | Hide / disable unfinished modules |

- Backend: `backend/app/platform/feature_registry.py` + `GET /api/v1/platform/features`
- Frontend: `frontend/src/config/feature-registry.ts` + permission-aware nav via `usePermissionAwareNavigation`

Unavailable features (`analytics`, `predictions`, `recommendations`, `reports`) are hidden from navigation automatically.

---

## Observability

| Capability | Detail |
|------------|--------|
| Prometheus | `GET /metrics` (`prometheus-client`) |
| Request metrics | Count + latency histogram by method / path template / status |
| Slow requests | Warning log + counter when duration ≥ `SLOW_REQUEST_MS` |
| Errors | 5xx / unhandled exception counters; auth failure counters |
| Health gauges | App ready / version / environment gauges set at lifespan |
| Request timing | `X-Response-Time-Ms` + `X-Request-ID` on every response |

Structured request completion logs include path, status, duration, and optional `user_id`.

---

## Tracing

OpenTelemetry SDK is integrated in `backend/app/observability/tracing.py`.

- Default: **disabled** (`OTEL_ENABLED=false`) — no collector required
- When enabled: TracerProvider + optional console exporter (`OTEL_CONSOLE_EXPORT`)
- Spans can be started via `start_span(...)` without forcing OTLP export

Wire an OTLP exporter in a later deployment step when a collector exists.

---

## Performance middleware

- **Gzip** compression (`GZipMiddleware`, threshold `GZIP_MINIMUM_SIZE`)
- **Cache-Control** on successful GET `/api/v1/*` (`private, max-age=…`)
- **Weak ETag** + `304 Not Modified` when response body is available
- Health/metrics use `Cache-Control: no-store`

---

## Configuration

| Environment | Notes |
|-------------|-------|
| Development / testing | `AUTH_REQUIRED=false`, weak JWT allowed, SQLite OK for tests |
| Production | Forces `AUTH_REQUIRED=true`, disables dev tokens, rejects DEBUG, SQLite, and weak JWT secrets (&lt; 32 chars / known placeholders) |

Production validation: `Settings._validate_production_secrets` and `config_production.assert_production_ready`.

See `backend/.env.example` for auth, metrics, OTEL, and cache knobs.

---

## OpenAPI

Enhanced via `attach_openapi`:

- Tag grouping (dashboard, sales, customers, operations, finance, platform, auth, health)
- Bearer security scheme
- Descriptions, response models, and error examples on platform/auth routes
- Global API description documenting JWT + backward-compatible anonymous mode

---

## Frontend integration

- Feature registry drives available modules
- Sidebar, command palette, and global search use permission-aware sections
- Dev roles: `NEXT_PUBLIC_DEV_ROLES` or `localStorage.edp.roles` (comma-separated) until IdP login exists
- Default role in local/dev: `admin` (full nav for demos)

---

## Deployment considerations

1. Set `APP_ENV=production`, `DEBUG=false`, strong `JWT_SECRET_KEY` (≥32 chars), PostgreSQL `DATABASE_URL`.
2. Terminate TLS at the edge; keep CORS origins explicit.
3. Scrape `/metrics` from Prometheus; do not expose metrics publicly without network controls.
4. Keep `/docs` internal or disable in hardened deployments if policy requires.
5. Enable OTEL only after configuring a collector; leave `OTEL_ENABLED=false` otherwise.
6. Frontend: point `NEXT_PUBLIC_API_BASE_URL` (or alias `NEXT_PUBLIC_API_URL`) at the API; configure roles only for non-prod demos.
7. Do not rely on `POST /api/v1/auth/dev-token` in production — it is disabled.
8. Roll out `AUTH_REQUIRED=true` only after clients can attach JWTs; until then stay on non-production env or explicit `AUTH_REQUIRED=false` (not recommended for public APIs).

---

## Compatibility guarantees

- Analytics service calculations unchanged
- Dashboard and feature page behavior unchanged
- Route handlers unchanged for permission logic (middleware-only protection)
- Existing anonymous API clients continue to work when auth is not required
