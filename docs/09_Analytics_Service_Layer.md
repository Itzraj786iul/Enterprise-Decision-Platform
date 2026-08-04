# Analytics Service Layer — Enterprise Decision Platform

Read-only analytics access infrastructure for PostgreSQL `analytics.*` views.  
**No dashboard routers, frontend, ML inference, or SQL view modifications in this phase.**

---

## Layer responsibilities

| Layer | Responsibility |
|-------|----------------|
| **View catalog** (`analytics/config.py`) | Maps logical keys → physical view names |
| **Query / validation** (`analytics/query.py`) | Filters, sort, pagination, date range, projection rules |
| **Repositories** (`analytics/repositories/`) | Read-only SQLAlchemy access to views only |
| **Services** (`analytics/services/`) | Validate inputs, orchestrate repos, return DTOs |
| **Schemas** (`schemas/analytics.py`) | KPI / trend / table / summary / pagination DTOs |
| **Caching** (`analytics/caching.py`) | `AnalyticsCache` protocol + `NullCache` (Redis later) |
| **DI** (`api/dependencies/analytics.py`) | Wire factory + services for future routers |

```text
Future API Router
    → Analytics Service (validation + DTO composition)
        → AnalyticsViewRepository (read-only)
            → PostgreSQL analytics.* views
                 ╳ never OLTP transactional tables
```

---

## Logical → physical view mapping

Services depend on **logical keys**, not physical names:

| Logical key | Default physical view |
|-------------|------------------------|
| `sales_summary` | `analytics.vw_sales_daily` |
| `sales_trends` | `analytics.vw_sales_monthly` |
| `fact_sales_line` | `analytics.vw_fact_sales_line` |
| `product_category_map` | `analytics.vw_product_category_map` |
| `customer_360` | `analytics.vw_customer_360` |
| `customer_rfm` | `analytics.vw_customer_rfm` |
| `inventory_summary` | `analytics.vw_inventory_health` |
| `supplier_performance` | `analytics.vw_supplier_performance` |
| `fact_return_line` | `analytics.vw_fact_return_line` |
| `shipment_performance` | `analytics.vw_shipment_performance` |
| `campaign_performance` | `analytics.vw_campaign_performance` |
| `payment_mix` | `analytics.vw_payment_mix` |
| `executive_scorecard` | `analytics.vw_executive_daily_kpis` |
| `machine_learning_predictions` | `analytics.vw_ml_predictions` (publish when ready) |
| `data_quality_summary` | `analytics.vw_data_quality_summary` (publish when ready) |

Override without code changes:

```env
ANALYTICS_SCHEMA=analytics
ANALYTICS_VIEW_OVERRIDES=sales_summary=vw_sales_daily_v2,customer_360=analytics.vw_customer_360_v2
```

---

## Repository capabilities

`AnalyticsViewRepository` supports:

- Filtering (`eq`, `ne`, `gt/gte`, `lt/lte`, `in`, `like`/`ilike`, null checks)
- Sorting (allowlisted columns)
- Pagination (`limit` / `offset` via page + page_size)
- Date range (allowlisted date columns)
- Search across configured searchable columns
- Column projection
- Streaming (`yield_per`) for large extracts
- Numeric SUM summaries for KPI composition

**No inserts/updates/deletes.** Autoload targets only the configured view.

---

## Services

| Service | Views used |
|---------|------------|
| `SalesAnalyticsService` | sales_summary, sales_trends |
| `CustomerAnalyticsService` | customer_360, customer_rfm |
| `FinanceAnalyticsService` | sales_summary, executive_scorecard |
| `OperationsAnalyticsService` | inventory, supplier, campaign |
| `ExecutiveAnalyticsService` | executive_scorecard |
| `MachineLearningService` | machine_learning_predictions (**read only**) |
| `DataQualityService` | data_quality_summary |
| `RecommendationService` | **Interface only** (unimplemented stub) |

Services contain **no SQL** and **no business KPI formulas** beyond repository aggregates / DTO shaping.

---

## Schemas (DTOs)

- `KpiCard`, `SummaryMetrics`
- `TrendPoint`, `TrendSeries`, `TimeSeriesResponse`
- `TableResult`, `AnalyticsTablePage`
- `AnalyticsQueryParams` / filter schemas
- `KpiDashboardBundle` (for future routers — not exposed yet)

---

## Caching (future Redis)

```python
class AnalyticsCache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
```

Services accept an `AnalyticsCache` (default `NullCache`).  
`build_cache_key()` hashes logical view + query payload. Swap in Redis without changing service method signatures.

---

## Scalability notes

1. Push filters/sort/limit into the view query — avoid loading full views in Python.
2. Use `stream()` + `yield_per` for exports.
3. Keep `ANALYTICS_MAX_PAGE_SIZE` bounded.
4. Prefer column projection for wide views.
5. Add Redis TTL caching for hot executive/sales summary queries later.
6. Scale read replicas at the database layer; services stay read-only.

---

## Testing

```bash
cd backend
pytest tests/test_analytics_query.py tests/test_analytics_repository.py tests/test_analytics_services.py -q
```

- Query validation: allowlists, date ranges, pagination
- Repository: SQLite stand-in tables (no Postgres required in unit tests)
- Services: mocked repositories (SQL-free orchestration)

---

## Out of scope

- Dashboard / analytics HTTP routers
- Frontend wiring
- ML model inference
- Changes to `sql/analytical_views.sql`
- Writes to OLTP or analytics views
