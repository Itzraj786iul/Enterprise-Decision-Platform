# 15 — Finance Intelligence

Complete vertical slice for financial analytics. Reuses the Analytics UI Framework and analytics service layer. Does **not** modify Executive, Sales, Customer, or Operations modules.

## Architecture

```
Browser (/finance)
  └─ FinanceIntelligencePage  (features/finance)
       ├─ Analytics UI Framework
       ├─ useAnalyticsFilters({ scope: "finance" })
       └─ TanStack Query → financeApi → FastAPI
            └─ /api/v1/finance/*
                 └─ FinanceService
                      └─ FinanceAnalyticsService
                           sales_summary, executive_scorecard,
                           payment_mix, campaign_performance
```

| Layer | Path |
|-------|------|
| API router | `backend/app/api/routes/finance.py` |
| Orchestrator | `backend/app/services/finance.py` |
| Schemas | `backend/app/schemas/finance.py` |
| Frontend client | `frontend/src/services/finance.ts` |
| Hooks | `frontend/src/features/finance/hooks/use-finance.ts` |
| Page | `frontend/src/features/finance/components/finance-intelligence-page.tsx` |
| Route | `frontend/src/app/(app)/finance/page.tsx` |

## Financial KPIs (`GET /overview`)

| Metric | Derivation | Source |
|--------|------------|--------|
| Revenue | Σ `net_sales` | `sales_summary` |
| Gross Profit | Σ `gross_profit` | `sales_summary` |
| Net Profit | Gross profit − refunds | sales + scorecard |
| Profit Margin | Gross profit / revenue | `sales_summary` |
| Operating Cost | COGS + discounts + refunds | sales + scorecard |
| Cost Ratio | Operating cost / revenue | derived |

`available=false` when source rows or denominators are missing.

## Profitability analytics (`GET /profitability`)

Regional rollup: revenue, COGS cost, gross profit, margin, growth vs prior window.

## Cost analytics (`GET /cost-breakdown`)

Categories from published commercial finance facts:

- **COGS** — `cogs_amount`
- **Discounts** — `discount_amount`
- **Refunds** — `refund_amount` (scorecard)

Includes share of total and trend vs prior period.

## Cashflow visualization (`GET /cashflow`)

Monthly periods with:

- **Inflows** — captured `payment_amount` (`payment_mix`), fallback to `net_sales`
- **Outflows** — COGS + discounts + refunds
- **Net cashflow** — inflows − outflows
- **Profit / margin** — included on the same period grain for profit & margin trend charts

## Budget variance (`GET /budget-variance`)

Uses `campaign_performance` budget vs actual spend, rolled up by `campaign_type` as **department**.

Returns budget, actual, variance, variance %.

## Financial risks (`GET /financial-risks`)

Derived from low-margin / contracting regions, rising cost categories, and budget overruns — with severity, estimated impact, owner, and recommendation.

## Filter behavior

| UI | State | API |
|----|-------|-----|
| Date | `dateRange` | `date_from` / `date_to` |
| Region | `regionIds` | `region` |
| Department | `productIds` (ProductFilter labeled Department) | `department` |
| Cost Category | `categoryIds` (CategoryFilter labeled Cost Category) | `cost_category` |
| Search | `search` | `search` |

## Component composition

Uses only Analytics UI Framework primitives:

- Layout / header / toolbar / filter bar / footer
- `AnalyticsKPIGrid`
- Trend — profit & margin lines; cashflow lines
- Comparison — regional profitability; budget vs actual
- Breakdown — cost composition pie
- Tables — budget detail + financial risks
- Insight / Recommendation panels

## Tests

| Suite | Coverage |
|-------|----------|
| `backend/tests/test_finance_api.py` | Overview, unavailable, profitability, costs, cashflow, risks, budget |
| `features/finance/hooks/use-finance.test.tsx` | Hook success + unavailable |
| `features/finance/components/finance-intelligence-page.test.tsx` | Render, Unavailable, Department / Cost Category filters |

## Related docs

- `docs/09_Analytics_Service_Layer.md`
- `docs/11_Analytics_UI_Framework.md`
- `docs/12`–`14` prior vertical slices
