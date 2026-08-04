# Backend Foundation — Enterprise Decision Platform

Production-ready FastAPI infrastructure for future analytics APIs.  
**This phase includes no analytics calculations, ML inference, or dashboard business endpoints.**

---

## Architecture

```text
app/
├── main.py                 create_app(), lifespan, middleware wiring
├── core/
│   ├── config.py           Settings + env validation (dev/test/prod)
│   ├── logging.py          Structured JSON logging
│   ├── middleware.py       Request ID + timing
│   ├── exceptions.py       AppError hierarchy
│   └── exception_handlers.py  Global HTTP error envelope
├── database/
│   ├── base.py             DeclarativeBase
│   └── session.py          Engine, pool, retry, session, shutdown
├── models/                 Abstract ORM bases + mixins only
├── schemas/                API envelopes (health, errors, pagination)
├── repositories/           Base / ReadOnly / CRUD generics
├── services/               Base / Read / CRUD interfaces
└── api/
    ├── dependencies/       DB, settings, logger, auth placeholder
    └── routes/health.py    /health /liveness /readiness /database
```

**Layering**

```text
Routes → Dependencies → Services → Repositories → SQLAlchemy Session → PostgreSQL
```

Business domains will plug into this stack later without changing the foundation.

---

## Configuration

`Settings` (`pydantic-settings`) loads from environment / `.env`.

| Environment | Notes |
|-------------|--------|
| `development` | Local DX; DB not required on startup by default |
| `testing` | Forces optional DB, non-JSON logs; used by pytest |
| `production` | Rejects weak `JWT_SECRET_KEY`, `DEBUG=true`, SQLite |

Important knobs:

- `DATABASE_URL`, pool size/overflow/timeout/recycle
- `DATABASE_CONNECT_RETRIES` / `DATABASE_CONNECT_RETRY_DELAY`
- `DATABASE_REQUIRED_ON_STARTUP`
- `LOG_LEVEL`, `LOG_JSON`
- `CORS_ORIGINS`

Copy `backend/.env.example` → `.env`.

---

## Database lifecycle

1. **Startup (`lifespan`)** — `configure_logging` → `init_database`  
   - Builds engine with pooling (`pool_pre_ping=True` for Postgres)  
   - Runs connectivity check with **tenacity** retries (`SELECT 1` only)  
   - Raises if `DATABASE_REQUIRED_ON_STARTUP=true` and DB is down  
2. **Request scope** — `get_db_session` dependency yields a session, commits on success, rollbacks on error, always closes  
3. **Shutdown** — `shutdown_database()` disposes the engine gracefully  

SQLAlchemy event hooks log **query duration** (`db_duration_ms`) for observability.

Alembic `env.py` points at `Base.metadata` and `DATABASE_URL`. No business migrations yet (abstract models only).

---

## Repository pattern

| Class | Role |
|-------|------|
| `BaseRepository` | Session + model type |
| `ReadOnlyRepository` | `get_by_id`, `list`, `count`, `exists` |
| `CRUDRepository` | `add`, `delete`, `soft_delete` |

No domain repositories (sales, customers, …) in this phase.

---

## Service layer

| Class | Role |
|-------|------|
| `BaseService` | Holds a repository |
| `ReadService` | Thin read façade |
| `CRUDService` | Thin write façade |

Services intentionally contain **no business rules** yet.

---

## Dependency injection

| Dependency | Purpose |
|------------|---------|
| `DbSession` | Request-scoped SQLAlchemy session |
| `AppSettings` | Cached settings |
| `RequestLogger` | LoggerAdapter with `request_id` |
| `CurrentUser` / `AuthenticatedUser` | Auth placeholder (anonymous) |

---

## Logging

- JSON logs in non-test environments (`LOG_JSON=true`)
- Middleware assigns **`X-Request-ID`**, measures **execution time**, emits access log with `duration_ms` and `db_duration_ms`
- Errors include `error_type` and stack traces for 500s

---

## Error handling

All errors use a standard envelope:

```json
{
  "success": false,
  "error": { "code": "not_found", "message": "...", "details": null },
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

Handled:

- `AppError` subclasses
- Pydantic / request validation → `422`
- HTTP 404
- SQLAlchemy errors → `503`
- Unhandled → `500`

---

## Health endpoints

| Path | Meaning |
|------|---------|
| `GET /health` | API process metadata |
| `GET /liveness` | Process up |
| `GET /readiness` | API + DB component status |
| `GET /database` | DB connectivity only |

Responses are infrastructure status — never KPI or analytics payloads.

---

## Models & schemas

**Models (abstract only)**

- Mixins: UUID PK, timestamps, audit, soft delete  
- Bases: `TimestampedModel`, `AuditedModel`, `SoftDeleteModel`

**Schemas**

- `BaseResponse`, `PaginatedResponse`, `ErrorResponse`, `HealthResponse`, `ResponseMeta`

---

## Testing

```bash
cd backend
# activate venv
pytest -q
ruff check .
```

Coverage includes configuration validation, health routes, DB connectivity (SQLite in tests), and generic CRUD repository behavior.

---

## Out of scope

- Analytics SQL / aggregations  
- ML inference endpoints  
- Dashboard business APIs  
- Concrete domain tables  

Next phases add domain models, repositories, and route modules on top of this foundation.
