# 14 — Operations Intelligence

Complete vertical slice for operations analytics. Reuses the Analytics UI Framework and analytics service layer. Does **not** modify Executive, Sales, or Customer modules.

## Architecture

```
Browser (/operations)
  └─ OperationsIntelligencePage  (features/operations)
       ├─ Analytics UI Framework
       ├─ useAnalyticsFilters({ scope: "operations" })
       └─ TanStack Query → operationsApi → FastAPI
            └─ /api/v1/operations/*
                 └─ OperationsService
                      ├─ OperationsAnalyticsService
                      │    inventory_summary, supplier_performance,
                      │    fact_return_line, shipment_performance
                      └─ SalesAnalyticsService
                           units_sold + store→region map + product categories
```

| Layer | Path |
|-------|------|
| API router | `backend/app/api/routes/operations.py` |
| Orchestrator | `backend/app/services/operations.py` |
| Schemas | `backend/app/schemas/operations.py` |
| Frontend client | `frontend/src/services/operations.ts` |
| Hooks | `frontend/src/features/operations/hooks/use-operations.ts` |
| Page | `frontend/src/features/operations/components/operations-intelligence-page.tsx` |
| Route | `frontend/src/app/(app)/operations/page.tsx` |

## Operational KPIs (`GET /overview`)

| Metric | Derivation | Source |
|--------|------------|--------|
| Inventory Value | Σ `inventory_value_cost` | `inventory_summary` |
| Inventory Health | % rows with `stock_status = Healthy` | `inventory_summary` |
| Stock Turnover | Σ `units_sold` / Σ `quantity_on_hand` | sales + inventory |
| Supplier Performance | Avg `on_time_rate` | `supplier_performance` |
| Return Rate | Σ returned qty / Σ units sold | returns + sales |
| Fulfillment Rate | % shipments `On Track` (or delivered) | `shipment_performance` |

`available=false` when the underlying view rows or denominators are missing. UI shows **Unavailable**.

## Inventory analytics (`GET /inventory`)

Supports pagination, sorting, projection, and search.

Returns product, category, stock (`quantity_on_hand`), safety stock (`reorder_point`), turnover (global units/on-hand rate when sales units exist), and inventory value.

Region filter maps `store_id` → region via sales summary.

## Supplier analytics (`GET /supplier-performance`)

| Field | Source column |
|-------|---------------|
| On-Time % | `on_time_rate` |
| Quality Score | `reliability_score` (normalized if > 1) |
| Lead Time | `avg_actual_lead_time_days` or contracted |
| Purchase Volume | `units_ordered` |
| Risk Level | Derived from on-time + quality thresholds |

## Returns analytics (`GET /returns`)

Joins return lines to `product_category_map` for category grain.

Returns count, share of returns (`return_pct`), refund cost, and trend vs prior window (up/down/flat).

## Warehouse performance (`GET /warehouse-performance`)

Combines inventory by `dc_name` / `store_name` with shipment fulfillment and average `fulfillment_lead_time_days`.

## Operational risks (`GET /operational-risks`)

Derived (not fabricated) from:

- Stockout / below-reorder inventory positions
- Suppliers with low on-time rate
- Categories with rising return trends

Each risk includes severity, owner, and recommendation.

## Filter behavior

| UI | State | API |
|----|-------|-----|
| Date | `dateRange` | `date_from` / `date_to` |
| Region | `regionIds` | `region` |
| Category | `categoryIds` | `category` |
| Supplier | `productIds` (ProductFilter labeled Supplier) | `supplier` |
| Search | `search` | `search` |

## Component composition

Uses only Analytics UI Framework primitives:

- Layout / header / toolbar / filter bar / footer
- `AnalyticsKPIGrid`
- Breakdown — inventory pie
- Comparison — supplier bars
- Trend — returns by category
- Breakdown — warehouse bars
- Tables — inventory detail + operational risks
- Insight / Recommendation panels

## Tests

| Suite | Coverage |
|-------|----------|
| `backend/tests/test_operations_api.py` | Overview, unavailable, inventory, suppliers, returns, warehouse, risks |
| `features/operations/hooks/use-operations.test.tsx` | Hook success + unavailable |
| `features/operations/components/operations-intelligence-page.test.tsx` | Render, Unavailable, Supplier filter |

## Related docs

- `docs/09_Analytics_Service_Layer.md`
- `docs/11_Analytics_UI_Framework.md`
- `docs/12_Sales_Intelligence.md`
- `docs/13_Customer_Intelligence.md`
