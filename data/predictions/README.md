# ML prediction CSV outputs

Persisted model outputs for `analytics.vw_ml_predictions` staging load.

| File | Model domain |
|------|----------------|
| `churn_predictions.csv` | Customer churn |
| `profit_predictions.csv` | Order profit prediction |
| `sales_forecast_predictions.csv` | Sales forecast |

Load into Neon (from repo root, after `sql/analytical_views.sql`):

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/load_ml_predictions.sql
```

Until loaded, `analytics.vw_ml_predictions` returns **zero rows** (no fabricated scores).
