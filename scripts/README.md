# Developer & deployment scripts

| Script | Purpose |
|--------|---------|
| `smoke-health.sh` | Local curl smoke for backend `/health` + frontend `/api/health` |
| `check_deployment.py` | Post-deploy verification (health, readiness, DB, metrics, API, headers, version) |

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
