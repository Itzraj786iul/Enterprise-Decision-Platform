# 12 — Sales Intelligence

Complete vertical slice for commercial analytics. Reuses the Analytics UI Framework and analytics service layer. Does **not** modify the Executive Dashboard.

## Architecture

```
Browser (/sales)
  └─ SalesIntelligencePage  (features/sales)
       ├─ Analytics UI Framework (layout, filters, sections, charts)
       ├─ useAnalyticsFilters / useAnalyticsSelection / useAnalyticsRefresh
       └─ TanStack Query hooks → salesApi → FastAPI
            └─ /api/v1/sales/*
                 └─ SalesService (orchestrator)
                      ├─ SalesAnalyticsService  (sales_summary, fact lines, category map)
                      └─ CustomerAnalyticsService (customer_360)
```

| Layer | Path |
|-------|------|
| API router | `backend/app/api/routes/sales.py` |
| Orchestrator | `backend/app/services/sales.py` |
| Schemas | `backend/app/schemas/sales.py` |
| Analytics extensions | `backend/app/analytics/services/sales.py`, `config.py` |
| Frontend client | `frontend/src/services/sales.ts` |
| Hooks | `frontend/src/features/sales/hooks/use-sales.ts` |
| Page | `frontend/src/features/sales/components/sales-intelligence-page.tsx` |
| Route | `frontend/src/app/(app)/sales/page.tsx` |

## API flow

Base path: `/api/v1/sales`

| Endpoint | Purpose | Primary sources |
|----------|---------|-----------------|
| `GET /overview` | Revenue, Orders, AOV, Gross Profit, Margin, Growth | `sales_summary` (`vw_sales_daily`) |
| `GET /trends?grain=` | Revenue / orders / profit series (`daily` \| `weekly` \| `monthly`) | `sales_summary` |
| `GET /category-performance` | Category, revenue, orders, growth, margin | `fact_sales_line` + `product_category_map` |
| `GET /product-performance` | Sorted / paginated / searchable / projected product rows | `fact_sales_line` + `product_category_map` |
| `GET /regional-performance` | Region, revenue, orders, growth | `sales_summary` |
| `GET /top-customers` | Customer, revenue, orders, lifetime value | `customer_360` |

Query filters (where applicable): `date_from`, `date_to`, `region` (CSV), `category` (CSV), `search`.

Product endpoint also supports: `page`, `page_size`, `sort_by`, `sort_dir`, `columns` (CSV projection).

### Availability contract

- Metrics use `available: false` when source rows are missing or a derived measure cannot be computed (e.g. growth without a prior window).
- Frontend displays **"Unavailable"** — never invents KPI values.
- Category / product endpoints set `available: false` when line or category-map views are unpublished or empty.

## Data flow

1. Filters from `useAnalyticsFilters({ scope: "sales" })` sync to URL (`from`, `to`, `region`, `category`, `q`) and localStorage.
2. Feature hooks map filters → `SalesQueryParams` and call `salesApi.*`.
3. `SalesService` builds `AnalyticsQuery` objects and calls analytics services only (no SQL in the orchestrator).
4. Aggregations (period windows, growth, AOV, margin, category/product rollups) happen in `SalesService` from analytics view rows.
5. UI maps response DTOs into Analytics Framework props (`AnalyticsKPIGrid` items, chart series, table rows).

## Filter behavior

| UI control | Filter state | API param |
|------------|--------------|-----------|
| Date range | `dateRange.start/end` | `date_from` / `date_to` |
| Region | `regionIds` | `region` |
| Category | `categoryIds` | `category` |
| Search | `search` | `search` |
| Reset | `resetFilters()` | Clears URL + persisted scope |

Region filtering applies on `sales_summary.region_name`. Category filtering applies on product L1 names for category/product endpoints; overview uses channel-name intersection as a soft commercial proxy when names match.

## Component composition

The page uses **only** Analytics UI Framework primitives:

- `AnalyticsPageLayout` / `AnalyticsHeader` / `AnalyticsToolbar` / `AnalyticsFilterBar` / `AnalyticsFooter`
- `AnalyticsKPIGrid`
- `AnalyticsTrendSection` + `AnalyticsLineChart` (revenue & orders)
- `AnalyticsComparisonSection` + `AnalyticsBarChart` (regional)
- `AnalyticsBreakdownSection` + `AnalyticsPieChart` (category)
- `AnalyticsTableSection` (top products, top customers)
- `AnalyticsInsightPanel` / `AnalyticsRecommendationPanel`

Insights and recommendations are derived from returned analytics payloads (growth, top region, weak region, top category). They do not introduce fabricated KPIs.

## Tests

| Suite | Coverage |
|-------|----------|
| `backend/tests/test_sales_api.py` | Overview (available + unavailable), trends grains, category, product sort/page/search, regional, top customers |
| `features/sales/hooks/use-sales.test.tsx` | Hook success + unavailable metric contract |
| `features/sales/components/sales-intelligence-page.test.tsx` | Page render, Unavailable label, filter bar |

## Constraints honored

- No duplicate analytics layouts or chart wrappers
- Executive Dashboard untouched
- No business calculations in the frontend
- No fabricated KPIs
- Read-only analytics services only

## Related docs

- `docs/09_Analytics_Service_Layer.md`
- `docs/10_Executive_Dashboard.md`
- `docs/11_Analytics_UI_Framework.md`
