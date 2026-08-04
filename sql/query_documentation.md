# SQL Analytics Layer — Query Documentation

| Attribute | Detail |
|-----------|--------|
| **Project** | Enterprise Business Analytics & Decision Intelligence Platform |
| **Folder** | `sql/` |
| **Engine** | PostgreSQL 14+ |
| **Depends on** | `database/schema.sql`, optionally `database/views.sql` |
| **Consumer tools** | Power BI, Streamlit, ad-hoc SQL, consulting packs |

---

## 1. How to deploy

```bash
# 1) Core OLTP
psql -d retail_analytics -f database/schema.sql
psql -d retail_analytics -f database/indexes.sql

# 2) Analytics layer
psql -d retail_analytics -f sql/analytical_views.sql
psql -d retail_analytics -f sql/stored_procedures.sql

# 3) Run selected queries interactively
psql -d retail_analytics -f sql/business_queries.sql
```

Set search path if needed:

```sql
SET search_path TO analytics, oltp, public;
```

---

## 2. File inventory

| File | Purpose |
|------|---------|
| `business_queries.sql` | 56 documented business questions with advanced SQL |
| `analytical_views.sql` | Reusable `analytics.*` views for Power BI / apps |
| `stored_procedures.sql` | Parameterized PostgreSQL functions for scorecards |
| `query_documentation.md` | This guide (semantics + performance) |

---

## 3. Analytical views (Power BI ready)

Connect Power BI to PostgreSQL and import/direct-query these objects:

| View | Grain | Primary use |
|------|-------|-------------|
| `analytics.vw_product_category_map` | Product | L1/L2 category attributes |
| `analytics.vw_fact_sales_line` | Order line | Core sales fact |
| `analytics.vw_sales_daily` | Date × store × channel | Daily commercial dashboard |
| `analytics.vw_sales_monthly` | Month | Trend / YoY |
| `analytics.vw_customer_360` | Customer | CRM / CLV / lifecycle |
| `analytics.vw_customer_rfm` | Customer | Segmentation |
| `analytics.vw_inventory_health` | Product × location | Stock status |
| `analytics.vw_fact_return_line` | Return line | Returns diagnostics |
| `analytics.vw_supplier_performance` | Supplier | Procurement scorecard |
| `analytics.vw_campaign_performance` | Campaign | Marketing ROI |
| `analytics.vw_shipment_performance` | Shipment | Fulfillment SLA |
| `analytics.vw_executive_daily_kpis` | Date | ExCo trend |
| `analytics.vw_payment_mix` | Method × month | Tender analytics |

**Power BI modeling tip:** Treat `vw_fact_sales_line` (or `vw_sales_daily`) as the fact and relate to calendar/store/product dimensions. Prefer Import mode on aggregated views for portfolio demos.

---

## 4. PostgreSQL functions

| Function | Parameters | Returns |
|----------|------------|---------|
| `analytics.fn_monthly_revenue(start, end)` | optional dates | Monthly sales + YoY |
| `analytics.fn_store_performance(start, end)` | required dates | Store league table |
| `analytics.fn_customer_rfm_asof(as_of)` | optional as-of date | RFM scores |
| `analytics.fn_category_contribution(start, end)` | required dates | Category Pareto |
| `analytics.fn_executive_scorecard(start, end)` | required dates | Single-row KPI snapshot |

Example:

```sql
SELECT * FROM analytics.fn_executive_scorecard('2026-01-01', '2026-03-31');
SELECT * FROM analytics.fn_store_performance('2026-01-01', '2026-03-31');
```

---

## 5. Business query catalog (56)

### Sales Analytics (Q01–Q17)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q01 | Monthly Revenue | GROUP BY | Monthly commercial pulse |
| Q02 | Quarterly Revenue | GROUP BY | Board/quarter packs |
| Q03 | YoY Growth | CTE + LAG(12) | True growth vs seasonality |
| Q04 | Sales by Region | Window share % | Territory investment |
| Q05 | Sales by Store | RANK(), productivity | Store accountability |
| Q06 | Sales by Product | Aggregates | Assortment focus |
| Q07 | Sales by Category | Category map view | Merch ownership |
| Q08 | Top 20 Products | DENSE_RANK | Protect hero SKUs |
| Q09 | Bottom 20 Products | DENSE_RANK ASC | Exit/markdown candidates |
| Q10 | Average Order Value | Monthly AOV | Basket productivity |
| Q11 | Basket Size | UPT / lines per order | Cross-sell health |
| Q12 | Sales Seasonality | Calendar attributes | Planning baselines |
| Q13 | Running Revenue | Cumulative window | Plan progress |
| Q14 | Rolling 3-Month Revenue | Moving sum/avg | Smoothed trend |
| Q15 | Revenue Contribution % | Cumulative Pareto | Concentration risk |
| Q16 | Region × Channel | GROUPING SETS | Omnichannel rollups |
| Q17 | MoM Growth | LAG / LEAD | Short-cycle momentum |

### Customer Analytics (Q18–Q28)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q18 | Customer Lifetime Value | 360 view | Value-based CRM |
| Q19 | RFM Metrics | NTILE segments | Campaign playbooks |
| Q20 | Repeat Purchase Rate | FILTER aggregates | Franchise health |
| Q21 | New vs Returning | CASE status | Growth quality |
| Q22 | Customer Cohorts | Cohort matrix | Retention curves |
| Q23 | Customer Retention | Period overlap | Base protection |
| Q24 | Churn Indicators | Lifecycle flags | Win-back priority |
| Q25 | Top Customers | ROW_NUMBER | VIP treatment |
| Q26 | Dormant Customers | Inactivity filter | Reactivation list |
| Q27 | Geographic Distribution | Region/state | Network/media fit |
| Q28 | Spend Percentiles | PERCENTILE_CONT | Concentration design |

### Finance Analytics (Q29–Q34)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q29 | Gross Profit | Monthly bridge | Profit dollars |
| Q30 | Profit Margin | Category × channel | Margin leakage |
| Q31 | Discount Analysis | Promo mix | Discount discipline |
| Q32 | Revenue vs Cost | Cost ratio | Price vs cost issues |
| Q33 | Payment Methods | Share windows | Tender economics |
| Q34 | Monthly Financial Summary | Sales + refunds | Close support |

### Operations Analytics (Q35–Q44)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q35 | Inventory Turnover | COGS / inventory proxy | Working capital |
| Q36 | Stock Coverage | Days of supply | Service vs capital |
| Q37 | Stockout Detection | Status + snapshot rate | Lost sales risk |
| Q38 | Supplier Performance | Fill / on-time | Vendor management |
| Q39 | Supplier Lead Time | Contracted vs actual | Planning buffers |
| Q40 | Store Performance | Sales per labor hour | Labor productivity |
| Q41 | Warehouse Performance | Delay rate | Fulfillment CX |
| Q42 | Shipment Delays | Exception list | Ops firefighting |
| Q43 | Return Rate | Units & value rates | Quality/CX fixes |
| Q44 | Return Cost | Reason economics | Profit leakage |

### Marketing Analytics (Q45–Q49)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q45 | Campaign ROI | Profit vs spend | Budget accountability |
| Q46 | Conversion Rate | Funnel rates | Targeting quality |
| Q47 | Revenue by Campaign | Attribution | Outcome linkage |
| Q48 | Campaign by Region | Geo split | Local offer fit |
| Q49 | Acquisition by Campaign | First-order join | CAC / growth engine |

### Executive KPIs (Q50–Q56)

| ID | Query | Techniques | Management takeaway |
|----|-------|------------|---------------------|
| Q50 | Executive Scorecard | Function call | ExCo one-pager |
| Q51 | Top Risks | UNION risk feed | Prioritized threats |
| Q52 | Best Opportunities | UNION opportunity feed | Growth agenda |
| Q53 | KPI Summary Dashboard | Key-value KPI feed | BI cards |
| Q54 | Category Hierarchy | Recursive CTE | Hierarchy integrity |
| Q55 | Same-Store Sales | Eligible stores + LAG | Comparable sales |
| Q56 | Channel Mix Trend | Moving average | Omnichannel shift |

---

## 6. Advanced SQL patterns used

| Pattern | Where used | Why |
|---------|------------|-----|
| CTEs | Most queries | Readable multi-step logic |
| Window functions | Running totals, ranks, shares | Avoid self-joins |
| `LAG` / `LEAD` | YoY, MoM, foresight | Period comparisons |
| `RANK` / `DENSE_RANK` / `ROW_NUMBER` | Leaderboards | Stable ordering |
| `NTILE` | RFM | Segment banding |
| `PERCENTILE_CONT` | Spend distribution | Tail risk |
| `GROUPING SETS` | Region × channel | Multi-level totals |
| `FILTER (WHERE …)` | Retention, funnels | Concise conditional aggs |
| Recursive CTE | Category tree | Hierarchy walk |
| Moving averages | Rolling 3-mo, channel mix | Noise reduction |
| `CASE` | Lifecycle, delay flags | Business rules in SQL |

---

## 7. Performance optimization recommendations

### 7.1 Indexes already recommended (`database/indexes.sql`)

Keep and verify these are applied before heavy analytics:

- `orders(order_date)`, `(customer_id)`, `(store_id)`, `(channel_id)`, `(campaign_id)`
- `order_items(order_id)`, `(product_id)`
- `inventory_snapshots(snapshot_date)`, `(product_id, snapshot_date)`
- `returns(return_date)`, `campaign_responses(campaign_id)`
- `purchase_orders(supplier_id, order_date)`

### 7.2 Additional indexes for this analytics layer

```sql
-- Composite supporting common sales mart filters
CREATE INDEX IF NOT EXISTS ix_orders_status_date
  ON oltp.orders (order_status, order_date);

-- Speeds customer 360 / RFM rebuilds
CREATE INDEX IF NOT EXISTS ix_orders_customer_date
  ON oltp.orders (customer_id, order_date);

-- Category contribution joins
CREATE INDEX IF NOT EXISTS ix_products_category_active
  ON oltp.products (category_id, is_active);

-- Snapshot stockout scans
CREATE INDEX IF NOT EXISTS ix_inv_snap_date_qty
  ON oltp.inventory_snapshots (snapshot_date, quantity_on_hand);
```

### 7.3 Query tuning guidance

1. **Filter early on `order_date` and `order_status`** — almost every commercial query should push these predicates down.
2. **Prefer `analytics.vw_sales_daily` / monthly views** for dashboards instead of rescanning `order_items` in Power BI visuals.
3. **Materialize hot paths** when Import mode is not enough:

```sql
CREATE MATERIALIZED VIEW analytics.mv_sales_daily AS
SELECT * FROM analytics.vw_sales_daily;

CREATE UNIQUE INDEX ON analytics.mv_sales_daily (order_date, store_id, channel_id);
-- Refresh after nightly load:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_sales_daily;
```

4. **Avoid correlated subqueries on large tables** (e.g., naive inventory valuation). Pre-join `products.current_unit_cost` once.
5. **Partition large facts** in production-scale deployments:
   - `orders` / `order_items` by month on `order_date`
   - `inventory_snapshots` by month on `snapshot_date`
6. **Analyze after bulk loads:**

```sql
ANALYZE oltp.orders;
ANALYZE oltp.order_items;
ANALYZE oltp.inventory_snapshots;
```

7. **Use `EXPLAIN (ANALYZE, BUFFERS)`** on Q03, Q22, Q35, Q37 before publishing to executives.
8. **RFM / cohort queries** are expensive at full scale — schedule as nightly tables, not interactive DirectQuery.
9. **Campaign response tables** can dominate I/O; aggregate to campaign-day marts for BI.
10. **Keep BI models skinny** — import aggregated marts, leave line-level for drill-through pages only.

### 7.4 Workload isolation

| Workload | Recommendation |
|----------|----------------|
| Executive dashboards | Materialized daily/monthly marts |
| CRM RFM | Nightly function → table |
| Ad-hoc diagnostics | Replica / read-only role |
| Inventory snapshot scans | Restrict to recent N days in interactive tools |

---

## 8. Metric definitions (canonical)

| KPI | Definition used in SQL |
|-----|------------------------|
| Net Sales | `SUM(order_items.line_net_amount)` |
| Gross Profit | Net Sales − `SUM(line_cogs_amount)` |
| Margin % | Gross Profit / Net Sales |
| AOV | Net Sales / distinct orders (or avg `orders.net_amount`) |
| Repeat Purchase Rate | Customers with ≥2 orders / customers with ≥1 order |
| Churn Risk | No purchase in >180 days (proxy) |
| Fill Rate | Units received / units ordered |
| Campaign ROI | (Attributed gross profit − spend) / spend |
| Return Rate (value) | Refund amount / net sales |

Align Power BI DAX measures to these SQL definitions to avoid KPI drift.

---

## 9. Consulting usage notes

- Run **Q50–Q53** for steering committee packs.
- Use **Q03/Q55** for growth quality debates (total vs same-store).
- Pair **Q19 + Q45** for CRM/marketing ROI narratives.
- Pair **Q37 + Q38** for supply-chain risk stories.
- Always cite the query ID in recommendation decks for auditability.

---

## 10. Out of scope (later phases)

- Python feature pipelines / ML scoring SQL
- Full Kimball star physical ETL scripts
- Row-level security policies in PostgreSQL
- Automated query regression tests

---

**Document owner:** Analytics Consulting Team  
**Next step:** Wire Power BI datasets to `analytics.vw_*` views and validate totals against `business_queries.sql` Q01/Q34.
