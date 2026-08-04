# 19 — Neon Production Database Deployment

Production PostgreSQL plan for the Enterprise Decision Platform on **Neon**.

**Backend (live bootstrap):** https://edp-api.onrender.com  
**GitHub:** https://github.com/Itzraj786iul/Enterprise-Decision-Platform  

This guide **does not** connect to Neon or change application code.  
SQL assets are **self-contained in this repository**.

Related: [17](./17_Deployment_Guide.md) · [18](./18_Production_Deployment.md) · [19 Render](./19_Render_Deployment.md)

---

## Repository structure (SQL packaging)

```text
enterprise-decision-platform/
├── database/
│   ├── schema.sql              # oltp tables
│   ├── indexes.sql
│   └── views.sql               # foundational oltp views
├── sql/
│   ├── analytical_views.sql    # analytics.vw_* (+ ML staging + DQ view)
│   ├── load_ml_predictions.sql # COPY CSVs → staging
│   ├── stored_procedures.sql   # optional
│   └── business_queries.sql    # docs only
├── data/
│   └── predictions/            # churn / profit / forecast CSVs
├── data_generation/            # synthetic OLTP CSV generator
└── backend/alembic/            # API baseline only (0001_baseline)
```

---

## Analytics SQL packaging

| Artifact | Role |
|----------|------|
| `sql/analytical_views.sql` | Creates `analytics` schema, KPI views, ML staging tables, `vw_ml_predictions`, `vw_data_quality_summary` |
| `sql/load_ml_predictions.sql` | Loads `data/predictions/*.csv` into staging (optional) |
| Empty staging | `vw_ml_predictions` returns **0 rows** — no fabricated scores |

### ML view — `analytics.vw_ml_predictions`

Unions real staging loads:

- Customer churn (`stg_churn_predictions`)
- Profit prediction (`stg_profit_predictions`)
- Sales forecast (`stg_sales_forecast_predictions`)

Columns include model name, entity, score, label, prediction timestamp, confidence (nullable), model version, prediction source.

### Data quality view — `analytics.vw_data_quality_summary`

Computes completeness, missing %, duplicates, freshness, validity, consistency, and overall DQ score **from `oltp` tables**. Empty OLTP → NULL overall score / empty metric usefulness without inventing numbers.

---

## Neon setup (summary)

1. Create Neon project (prefer region near Render Oregon)  
2. Create database  
3. Use **pooled** URL for Render, **direct** for `psql`/Alembic  
4. Always `sslmode=require`  

---

## Deployment sequence

From **repository root**:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@DIRECT_HOST/DB?sslmode=require"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/indexes.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/views.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/analytical_views.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/stored_procedures.sql   # optional

# OLTP data
python -m data_generation.generate_all --demo
# then COPY/load generated CSVs into oltp.*

# Optional ML outputs
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/load_ml_predictions.sql

cd backend
alembic upgrade head
```

Then point Render `DATABASE_URL` at Neon (pooled), set `APP_ENV=production`, health `/readiness`.

---

## Catalog confirmation

| Logical key | Physical view |
|-------------|----------------|
| sales_summary | `analytics.vw_sales_daily` |
| sales_trends | `analytics.vw_sales_monthly` |
| customer_360 | `analytics.vw_customer_360` |
| customer_rfm | `analytics.vw_customer_rfm` |
| inventory_summary | `analytics.vw_inventory_health` |
| supplier_performance | `analytics.vw_supplier_performance` |
| campaign_performance | `analytics.vw_campaign_performance` |
| executive_scorecard | `analytics.vw_executive_daily_kpis` |
| machine_learning_predictions | `analytics.vw_ml_predictions` |
| data_quality_summary | `analytics.vw_data_quality_summary` |

---

## Verification queries

```sql
SELECT COUNT(*) FROM information_schema.views
WHERE table_schema = 'analytics' AND table_name IN (
  'vw_ml_predictions', 'vw_data_quality_summary', 'vw_sales_daily'
);

SELECT * FROM alembic_version;  -- 0001_baseline
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSL | `?sslmode=require` |
| Timeout | Prefer pooled app URL; wake Neon compute |
| View create fail | Ensure `schema.sql` applied first |
| Empty ML view | Run `sql/load_ml_predictions.sql` |
| Permission | Use Neon owner role |
