# 13 — Customer Intelligence

Complete vertical slice for customer analytics. Reuses the Analytics UI Framework and analytics service layer. Does **not** modify Executive Dashboard or Sales Intelligence.

## Architecture

```
Browser (/customers)
  └─ CustomerIntelligencePage  (features/customers)
       ├─ Analytics UI Framework (layout, filters, sections, charts)
       ├─ useAnalyticsFilters({ scope: "customers" })
       └─ TanStack Query → customersApi → FastAPI
            └─ /api/v1/customers/*
                 └─ CustomerService
                      ├─ CustomerAnalyticsService  (customer_360, customer_rfm)
                      ├─ SalesAnalyticsService     (store → region map)
                      └─ MachineLearningService    (churn predictions)
```

| Layer | Path |
|-------|------|
| API router | `backend/app/api/routes/customers.py` |
| Orchestrator | `backend/app/services/customers.py` |
| Schemas | `backend/app/schemas/customers.py` |
| Frontend client | `frontend/src/services/customers.ts` |
| Hooks | `frontend/src/features/customers/hooks/use-customers.ts` |
| Page | `frontend/src/features/customers/components/customer-intelligence-page.tsx` |
| Route | `frontend/src/app/(app)/customers/page.tsx` |

## API flow

Base path: `/api/v1/customers`

| Endpoint | Returns | Sources |
|----------|---------|---------|
| `GET /overview` | Active / New / Repeat customers, Avg LTV, Retention, Churn risk summary | `customer_360` (+ RFM/region filters) |
| `GET /rfm-segments` | Segment, count, revenue, AOV, growth | `customer_rfm` + `customer_360` |
| `GET /cohorts` | Monthly cohorts, retention %, counts | `customer_360` (`first_order_date` / `last_order_date`) |
| `GET /customer-distribution` | Region, count, revenue, growth | `customer_360` + store→region from `sales_summary` |
| `GET /top-customers` | Sort / page / search / projection | `customer_360` + RFM segment |
| `GET /churn-risk` | Risk level, count, revenue at risk, confidence | ML predictions, lifecycle fallback |

Filters: `date_from`, `date_to`, `region`, `segment`, `search`.

Unavailable metrics and empty marts use `available: false`. The UI shows **Unavailable** — never invents values.

## Data flow

1. Filters sync via URL (`from`, `to`, `region`, `category`→segment, `q`) and `localStorage` scope `customers`.
2. Feature hooks map filters to `CustomerQueryParams` (`segmentIds` from `categoryIds`).
3. `CustomerService` reads analytics views only; aggregations (retention, cohorts, RFM rollups, risk buckets) run in the orchestrator.
4. Responses map into Analytics Framework props (KPI items, chart series, tables).

## Filter behavior

| UI control | State | API |
|------------|-------|-----|
| Date range | `dateRange` | `date_from` / `date_to` |
| Region | `regionIds` | `region` (via preferred store → region) |
| Customer Segment | `categoryIds` (labeled Segment) | `segment` (RFM) |
| Search | `search` | `search` |

`CategoryFilter` accepts an optional `label` so the shared control renders as **Customer Segment** without a duplicated filter component.

## RFM model integration

- Logical view: `customer_rfm` → `analytics.vw_customer_rfm`
- Segments come from `rfm_segment` (Champions, Loyal, Promising New, At Risk Loyal, Hibernating, Need Attention, …)
- Revenue / counts roll up from RFM rows; AOV prefers `customer_360.avg_order_value`
- Growth compares period-active revenue (by `last_order_date`) vs the prior window when both sides exist; otherwise `growth` is null

## Cohort visualization

- Cohort key = month of `first_order_date`
- Retention at month offset `k` = share of cohort members with `last_order_date >= cohort_month + k`
- API returns `retentions[{ month_offset, retention_pct, customer_count }]`
- UI: line chart for the latest cohort curve + matrix table (M0–M3)

This is a first/last-order approximation suitable when no order-event mart is registered — still derived from analytics rows, not fabricated.

## Component composition

Uses only Analytics UI Framework primitives:

- Layout / header / toolbar / filter bar / footer
- `AnalyticsKPIGrid`
- `AnalyticsBreakdownSection` — RFM pie + bar, regional bar, churn bar
- `AnalyticsTrendSection` — cohort retention curve
- `AnalyticsTableSection` — cohort matrix + top customers
- `AnalyticsInsightPanel` / `AnalyticsRecommendationPanel`

Insights/recommendations are narrative over returned payloads (retention, top RFM segment, high churn) — not new KPIs.

## Tests

| Suite | Coverage |
|-------|----------|
| `backend/tests/test_customers_api.py` | Overview, unavailable, RFM, cohorts, distribution, top customers, churn |
| `features/customers/hooks/use-customers.test.tsx` | Hook success + unavailable contract |
| `features/customers/components/customer-intelligence-page.test.tsx` | Render, Unavailable, segment filter label |

## Constraints honored

- Executive and Sales modules untouched
- No duplicated layouts or chart wrappers
- No frontend business calculations
- No fabricated metrics
- Read-only analytics services only

## Related docs

- `docs/09_Analytics_Service_Layer.md`
- `docs/11_Analytics_UI_Framework.md`
- `docs/12_Sales_Intelligence.md`
