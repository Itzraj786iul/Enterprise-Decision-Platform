# Executive Dashboard — Vertical Slice

First complete business feature for the Enterprise Decision Platform.

---

## Architecture

```text
Frontend /dashboard
  → TanStack Query hooks
    → services/dashboard.ts
      → GET /api/v1/dashboard/*
        → DashboardService
          → ExecutiveAnalyticsService
          → DataQualityService
          → MachineLearningService (read-only predictions)
            → AnalyticsViewRepository
              → analytics.* SQL views
```

No SQL in routers/services beyond the existing read-only repository stack.  
No repository API changes for this slice (service orchestration only).

---

## API flow

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/dashboard/overview` | KPI cards for the executive period |
| `GET /api/v1/dashboard/trends` | Revenue / profit / orders daily series |
| `GET /api/v1/dashboard/regional-performance` | Region rollups |
| `GET /api/v1/dashboard/top-risks` | DQ + ML + inventory risk signals |
| `GET /api/v1/dashboard/opportunities` | ML opportunity signals + margin trajectory |

Query params: `days` (overview/trends/regional), `limit` (risks/opportunities).

---

## Frontend flow

1. `ExecutiveDashboard` mounts under AppShell.
2. Hooks (`useDashboardOverview`, `useDashboardTrends`, …) fetch in parallel via TanStack Query (retry=2, staleTime=60s).
3. Presentational feature components compose design-system primitives:
   - `MetricCard`, `ChartCard`, `DataTable`, `InsightCard`, `RecommendationCard`, `AlertCard`
   - `LoadingSpinner`, `EmptyState`, `ErrorState`
4. Refresh action invalidates/refetches all queries.

---

## Data flow & KPI derivation

All values come from analytics service outputs. Unavailable sources return `available: false` (UI shows **Unavailable**) — no fabricated KPIs.

| KPI | Derivation |
|-----|------------|
| Revenue | Σ `net_sales` on executive scorecard (current window) |
| Profit | Σ `gross_profit` |
| Profit Margin | Profit / Revenue |
| Revenue Growth | Current vs prior equal-length window |
| Active Customers | Distinct customer entities in ML prediction rows (when present) |
| Inventory Health | `1 - stockouts/positions` from scorecard |
| DQ Score | From `DataQualityService` (overall/average score) |
| Overall Churn Risk | Mean churn-model scores from ML predictions |

Trends read daily scorecard rows. Regional performance aggregates `SALES_SUMMARY` rows (via `ExecutiveAnalyticsService.get_commercial_detail`) by `region_name`.

Risks/opportunities map **existing** DQ severity and ML labels/scores — they do not invent narratives without source rows.

---

## Visual hierarchy

1. Page header + refresh  
2. Executive KPI row (8 cards)  
3. Revenue / profit / orders trend chart  
4. Regional performance table  
5. Risks | Opportunities (two-column)  
6. DQ summary insight  

---

## States

- **Loading**: skeletons / spinners per panel  
- **Empty**: `EmptyState` when arrays are empty  
- **Error**: `ErrorState` with retry  
- **Success**: populated panels  

---

## Accessibility

- Section `aria-label`s  
- Chart `role="img"` via `ChartContainer`  
- Keyboard-focusable refresh / retry controls  
- Responsive grids (1 → 2 → 4 columns)

---

## Testing

```bash
# Backend
cd backend && pytest tests/test_dashboard_api.py -q

# Frontend
cd frontend && npm run test
```

---

## Out of scope

- Other dashboards (sales/customer/…)  
- Recommendation engine implementation  
- ML inference  
- Changes to SQL views
