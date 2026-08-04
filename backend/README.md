# Backend — Enterprise Decision Platform

FastAPI backend **infrastructure foundation**.

No analytics, ML, or dashboard business APIs in this phase.

## Quick start

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health:

- `GET /health`
- `GET /liveness`
- `GET /readiness`
- `GET /database`

## Analytics access layer

Read-only repositories/services over `analytics.*` views (no dashboard routers yet).  
See `../docs/09_Analytics_Service_Layer.md`.

## Quality

```bash
ruff check .
pytest -q
```

## Docs

See `../docs/08_Backend_Foundation.md`.
