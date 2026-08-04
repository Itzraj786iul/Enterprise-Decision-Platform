# Developer & deployment scripts

| Script | Purpose |
|--------|---------|
| `load_database.py` | Bulk-load `data/generated/*.csv` into PostgreSQL `oltp` via COPY |
| `smoke-health.sh` | Local curl smoke for backend `/health` + frontend `/api/health` |
| `check_deployment.py` | Post-deploy verification (health, readiness, DB, metrics, API, headers, version) |

## OLTP data load

```bash
# From repo root — Neon direct URL recommended
set DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require

python scripts/load_database.py --data-dir "E:/Conulsting project/data/generated" --truncate

python scripts/load_database.py --data-dir "E:/Conulsting project/data/generated" --dry-run --verbose
```

Full guide: [docs/20_Data_Loading.md](../docs/20_Data_Loading.md).

## Deployment verification

```bash
# From repo root — after Render is live
python scripts/check_deployment.py --base-url https://<api>.onrender.com

# With JWT (production AUTH_REQUIRED=true)
python scripts/check_deployment.py --base-url https://<api>.onrender.com --token "$JWT"

# Skip protected analytics probes
python scripts/check_deployment.py --base-url https://<api>.onrender.com --skip-auth
```

Exit code `0` = pass, `1` = failed checks.

Full sequence: [docs/18_Production_Deployment.md](../docs/18_Production_Deployment.md).
