-- =============================================================================
-- Enterprise Business Analytics & Decision Intelligence Platform
-- Business Analytics Queries (55+)
-- =============================================================================
-- Prerequisite: database/schema.sql and sql/analytical_views.sql
-- Schema: analytics + oltp
-- Each query includes: Business Objective | SQL | Interpretation | Why Care
-- =============================================================================

SET search_path TO analytics, oltp, public;

-- #############################################################################
-- SECTION A — SALES ANALYTICS
-- #############################################################################

/* Q01 | Monthly Revenue
   Business objective: Track net sales by calendar month for trend monitoring.
   Business interpretation: Rising months indicate demand strength; dips flag seasonality or issues.
   Why management should care: Primary commercial pulse used in monthly business reviews. */
SELECT
    d.year_number,
    d.month_number,
    d.month_name,
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    COUNT(DISTINCT o.order_id) AS order_count
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
JOIN oltp.calendar_date d ON d.full_date = o.order_date
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY d.year_number, d.month_number, d.month_name, DATE_TRUNC('month', o.order_date)::DATE
ORDER BY month_start;


/* Q02 | Quarterly Revenue
   Business objective: Summarize commercial performance by fiscal/calendar quarter.
   Business interpretation: Quarter totals support board packs and forecast variance reviews.
   Why management should care: Aligns reporting to executive quarterly cadence. */
SELECT
    d.year_number,
    d.quarter_number,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(SUM(oi.line_net_amount - oi.line_cogs_amount), 2) AS gross_profit,
    COUNT(DISTINCT o.order_id) AS order_count
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
JOIN oltp.calendar_date d ON d.full_date = o.order_date
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY d.year_number, d.quarter_number
ORDER BY d.year_number, d.quarter_number;


/* Q03 | Year-over-Year Growth
   Business objective: Compare each month to the same month prior year.
   Business interpretation: Positive YoY = underlying growth; negative needs driver diagnosis.
   Why management should care: Separates true growth from seasonal noise. */
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1
)
SELECT
    month_start,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(LAG(net_sales, 12) OVER (ORDER BY month_start), 2) AS prior_year_sales,
    ROUND(
        (net_sales - LAG(net_sales, 12) OVER (ORDER BY month_start))
        / NULLIF(LAG(net_sales, 12) OVER (ORDER BY month_start), 0),
        4
    ) AS yoy_growth_pct
FROM monthly
ORDER BY month_start;


/* Q04 | Sales by Region
   Business objective: Allocate net sales across management regions.
   Business interpretation: Highlights geographic concentration and underperforming territories.
   Why management should care: Guides regional investment, staffing, and assortment. */
SELECT
    r.region_code,
    r.region_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(
        SUM(oi.line_net_amount) / SUM(SUM(oi.line_net_amount)) OVER (),
        4
    ) AS region_share_pct
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
JOIN oltp.stores s ON s.store_id = o.store_id
JOIN oltp.regions r ON r.region_id = s.region_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY r.region_code, r.region_name
ORDER BY net_sales DESC;


/* Q05 | Sales by Store
   Business objective: Rank stores by net sales and productivity.
   Business interpretation: Identifies top/bottom quartile locations for action planning.
   Why management should care: Store P&L accountability and capital allocation. */
SELECT
    s.store_id,
    s.store_code,
    s.store_name,
    s.store_format,
    r.region_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(SUM(oi.line_net_amount) / NULLIF(s.selling_sq_ft, 0), 2) AS sales_per_sqft,
    RANK() OVER (ORDER BY SUM(oi.line_net_amount) DESC) AS sales_rank
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
JOIN oltp.stores s ON s.store_id = o.store_id
JOIN oltp.regions r ON r.region_id = s.region_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY s.store_id, s.store_code, s.store_name, s.store_format, r.region_name, s.selling_sq_ft
ORDER BY net_sales DESC;


/* Q06 | Sales by Product
   Business objective: Measure SKU-level net sales and units.
   Business interpretation: Surfaces hero SKUs vs slow movers for assortment decisions.
   Why management should care: Assortment productivity drives margin and inventory turns. */
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    SUM(oi.quantity) AS units_sold,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM oltp.order_items oi
JOIN oltp.orders o ON o.order_id = oi.order_id
JOIN oltp.products p ON p.product_id = oi.product_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY p.product_id, p.sku, p.product_name
ORDER BY net_sales DESC;


/* Q07 | Sales by Category
   Business objective: Roll sales to L1 category for merchandising scorecards.
   Business interpretation: Category mix shifts signal demand or pricing changes.
   Why management should care: Category managers own growth and margin targets. */
SELECT
    pcm.category_code,
    pcm.category_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(SUM(oi.line_net_amount - oi.line_cogs_amount), 2) AS gross_profit,
    SUM(oi.quantity) AS units_sold
FROM oltp.order_items oi
JOIN oltp.orders o ON o.order_id = oi.order_id
JOIN analytics.vw_product_category_map pcm ON pcm.product_id = oi.product_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY pcm.category_code, pcm.category_name
ORDER BY net_sales DESC;


/* Q08 | Top 20 Products
   Business objective: Identify the highest-revenue SKUs.
   Business interpretation: Protect availability and marketing support for these items.
   Why management should care: A small set of SKUs often drives disproportionate revenue. */
SELECT *
FROM (
    SELECT
        p.sku,
        p.product_name,
        ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
        SUM(oi.quantity) AS units_sold,
        DENSE_RANK() OVER (ORDER BY SUM(oi.line_net_amount) DESC) AS sales_rank
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    JOIN oltp.products p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY p.sku, p.product_name
) x
WHERE sales_rank <= 20
ORDER BY sales_rank;


/* Q09 | Bottom 20 Products (with meaningful volume filter)
   Business objective: Find lowest-selling active SKUs for rationalization.
   Business interpretation: Candidates for markdown, exit, or localization.
   Why management should care: Slow movers inflate inventory and suppress turns. */
SELECT *
FROM (
    SELECT
        p.sku,
        p.product_name,
        ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
        SUM(oi.quantity) AS units_sold,
        DENSE_RANK() OVER (ORDER BY SUM(oi.line_net_amount) ASC) AS sales_rank_asc
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    JOIN oltp.products p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
      AND p.is_active = TRUE
    GROUP BY p.sku, p.product_name
    HAVING SUM(oi.quantity) >= 5
) x
WHERE sales_rank_asc <= 20
ORDER BY sales_rank_asc;


/* Q10 | Average Order Value (AOV)
   Business objective: Monitor basket value over time.
   Business interpretation: Rising AOV may reflect mix/upsell; falling AOV can signal traffic quality issues.
   Why management should care: AOV is a core commercial productivity KPI. */
SELECT
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    ROUND(SUM(o.net_amount) / NULLIF(COUNT(*), 0), 2) AS aov,
    COUNT(*) AS order_count
FROM oltp.orders o
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY 1
ORDER BY 1;


/* Q11 | Basket Size (Units per Transaction)
   Business objective: Measure units per order (UPT).
   Business interpretation: Low UPT suggests weak cross-sell or assortment gaps.
   Why management should care: Basket expansion is a high-ROI growth lever. */
SELECT
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    ROUND(SUM(oi.quantity)::NUMERIC / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS units_per_transaction,
    ROUND(COUNT(oi.order_item_id)::NUMERIC / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS lines_per_order
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY 1
ORDER BY 1;


/* Q12 | Sales Seasonality
   Business objective: Quantify demand by season and weekday pattern.
   Business interpretation: Peaks in Holiday/weekend inform staffing, inventory, and campaigns.
   Why management should care: Planning accuracy depends on seasonal baselines. */
SELECT
    d.season_name,
    d.day_name,
    d.is_weekend,
    ROUND(AVG(day_sales.net_sales), 2) AS avg_daily_net_sales
FROM (
    SELECT o.order_date, SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY o.order_date
) day_sales
JOIN oltp.calendar_date d ON d.full_date = day_sales.order_date
GROUP BY d.season_name, d.day_name, d.is_weekend, d.day_of_week
ORDER BY d.season_name, d.day_of_week;


/* Q13 | Running Revenue (Window Functions)
   Business objective: Compute cumulative net sales over time.
   Business interpretation: Cumulative curve shows progress to annual plan.
   Why management should care: Enables plan-vs-actual tracking mid-year. */
WITH daily AS (
    SELECT
        o.order_date,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY o.order_date
)
SELECT
    order_date,
    ROUND(net_sales, 2) AS daily_net_sales,
    ROUND(SUM(net_sales) OVER (ORDER BY order_date
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM daily
ORDER BY order_date;


/* Q14 | Rolling 3-Month Revenue
   Business objective: Smooth short-term noise with a 3-month moving sum/average.
   Business interpretation: Trend direction without overreacting to one weak month.
   Why management should care: Supports steadier forecasting and inventory buys. */
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1
)
SELECT
    month_start,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(SUM(net_sales) OVER (
        ORDER BY month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3mo_revenue,
    ROUND(AVG(net_sales) OVER (
        ORDER BY month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3mo_avg
FROM monthly
ORDER BY month_start;


/* Q15 | Revenue Contribution %
   Business objective: Show each category's share of total revenue (Pareto-ready).
   Business interpretation: Cumulative % highlights concentration risk.
   Why management should care: Over-reliance on few categories increases downside risk. */
WITH cat AS (
    SELECT
        pcm.category_name,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    JOIN analytics.vw_product_category_map pcm ON pcm.product_id = oi.product_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY pcm.category_name
)
SELECT
    category_name,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(net_sales / SUM(net_sales) OVER (), 4) AS contribution_pct,
    ROUND(SUM(net_sales) OVER (ORDER BY net_sales DESC) / SUM(net_sales) OVER (), 4) AS cumulative_pct
FROM cat
ORDER BY net_sales DESC;


/* Q16 | Sales with GROUPING SETS (Region × Channel rollups)
   Business objective: Produce region, channel, and combined subtotals in one pass.
   Business interpretation: Cross-tab view for omnichannel strategy discussions.
   Why management should care: Faster multi-level reporting without multiple queries. */
SELECT
    COALESCE(r.region_name, 'ALL REGIONS') AS region_name,
    COALESCE(ch.channel_name, 'ALL CHANNELS') AS channel_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    GROUPING(r.region_name) AS is_region_total,
    GROUPING(ch.channel_name) AS is_channel_total
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
LEFT JOIN oltp.stores s ON s.store_id = o.store_id
LEFT JOIN oltp.regions r ON r.region_id = s.region_id
JOIN oltp.channels ch ON ch.channel_id = o.channel_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY GROUPING SETS (
    (r.region_name, ch.channel_name),
    (r.region_name),
    (ch.channel_name),
    ()
)
ORDER BY is_region_total, region_name, is_channel_total, channel_name;


/* Q17 | MoM Growth with LAG
   Business objective: Month-over-month sales change.
   Business interpretation: Short-cycle momentum indicator for commercial huddles.
   Why management should care: Early warning for sudden demand shifts. */
WITH monthly AS (
    SELECT DATE_TRUNC('month', o.order_date)::DATE AS month_start,
           SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1
)
SELECT
    month_start,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(LAG(net_sales) OVER (ORDER BY month_start), 2) AS prior_month,
    ROUND(
        (net_sales - LAG(net_sales) OVER (ORDER BY month_start))
        / NULLIF(LAG(net_sales) OVER (ORDER BY month_start), 0),
        4
    ) AS mom_growth_pct,
    ROUND(LEAD(net_sales) OVER (ORDER BY month_start), 2) AS next_month_sales
FROM monthly
ORDER BY month_start;


-- #############################################################################
-- SECTION B — CUSTOMER ANALYTICS
-- #############################################################################

/* Q18 | Customer Lifetime Value (Historical)
   Business objective: Estimate historical CLV as lifetime gross profit (or net sales).
   Business interpretation: High-CLV customers deserve retention investment.
   Why management should care: Value-based CRM beats equal treatment of all shoppers. */
SELECT
    customer_id,
    customer_number,
    customer_type,
    loyalty_tier,
    order_count,
    ROUND(lifetime_net_sales, 2) AS lifetime_net_sales,
    ROUND(lifetime_gross_profit, 2) AS historical_clv,
    lifecycle_status
FROM analytics.vw_customer_360
WHERE order_count IS NOT NULL
ORDER BY lifetime_gross_profit DESC NULLS LAST
LIMIT 100;


/* Q19 | RFM Metrics
   Business objective: Score customers on Recency, Frequency, Monetary value.
   Business interpretation: Segments like Champions vs Hibernating drive playbooks.
   Why management should care: Improves campaign ROI and retention efficiency. */
SELECT
    rfm_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(lifetime_net_sales), 2) AS avg_monetary,
    ROUND(AVG(order_count), 2) AS avg_frequency,
    ROUND(AVG(days_since_last_order), 1) AS avg_recency_days
FROM analytics.vw_customer_rfm
GROUP BY rfm_segment
ORDER BY customer_count DESC;


/* Q20 | Repeat Purchase Rate
   Business objective: Share of customers with 2+ orders.
   Business interpretation: Higher repeat rate = healthier franchise.
   Why management should care: Retention usually cheaper than acquisition. */
WITH cust AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS orders
    FROM oltp.orders
    WHERE order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS customers_with_orders,
    COUNT(*) FILTER (WHERE orders >= 2) AS repeat_customers,
    ROUND(COUNT(*) FILTER (WHERE orders >= 2)::NUMERIC / NULLIF(COUNT(*), 0), 4) AS repeat_purchase_rate
FROM cust;


/* Q21 | New vs Returning Customers (monthly)
   Business objective: Split monthly buyers into first-time vs returning.
   Business interpretation: Growth quality — new acquisition vs base reactivation.
   Why management should care: Diagnoses whether growth is durable. */
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM oltp.orders
    WHERE order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY customer_id
),
monthly_buyers AS (
    SELECT DISTINCT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        o.customer_id,
        CASE WHEN DATE_TRUNC('month', o.order_date) = DATE_TRUNC('month', f.first_order_date)
             THEN 'New' ELSE 'Returning' END AS customer_status
    FROM oltp.orders o
    JOIN first_order f ON f.customer_id = o.customer_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
)
SELECT
    month_start,
    customer_status,
    COUNT(*) AS customers
FROM monthly_buyers
GROUP BY month_start, customer_status
ORDER BY month_start, customer_status;


/* Q22 | Customer Cohorts (first-order month retention matrix sample)
   Business objective: Track retention by acquisition cohort over subsequent months.
   Business interpretation: Steep drop-offs highlight onboarding/experience issues.
   Why management should care: Cohort curves are the gold standard for retention health. */
WITH first_order AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_date))::DATE AS cohort_month
    FROM oltp.orders
    WHERE order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        o.customer_id,
        DATE_TRUNC('month', o.order_date)::DATE AS activity_month
    FROM oltp.orders o
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
)
SELECT
    f.cohort_month,
    a.activity_month,
    (EXTRACT(YEAR FROM age(a.activity_month, f.cohort_month)) * 12
      + EXTRACT(MONTH FROM age(a.activity_month, f.cohort_month)))::INT AS months_since_acquisition,
    COUNT(DISTINCT f.customer_id) AS active_customers
FROM first_order f
JOIN activity a ON a.customer_id = f.customer_id
GROUP BY f.cohort_month, a.activity_month
ORDER BY f.cohort_month, a.activity_month;


/* Q23 | Customer Retention (period-over-period)
   Business objective: % of prior-period buyers who purchased again in current period.
   Business interpretation: Retention decline is an early churn signal.
   Why management should care: Protects the installed customer base. */
WITH params AS (
    SELECT
        DATE_TRUNC('month', MAX(order_date))::DATE AS current_month
    FROM oltp.orders
),
windows AS (
    SELECT
        current_month,
        (current_month - INTERVAL '1 month')::DATE AS prior_month
    FROM params
),
prior_buyers AS (
    SELECT DISTINCT o.customer_id
    FROM oltp.orders o
    CROSS JOIN windows w
    WHERE DATE_TRUNC('month', o.order_date)::DATE = w.prior_month
),
current_buyers AS (
    SELECT DISTINCT o.customer_id
    FROM oltp.orders o
    CROSS JOIN windows w
    WHERE DATE_TRUNC('month', o.order_date)::DATE = w.current_month
)
SELECT
    (SELECT prior_month FROM windows) AS prior_month,
    (SELECT current_month FROM windows) AS current_month,
    COUNT(*) AS prior_buyers,
    COUNT(*) FILTER (WHERE cb.customer_id IS NOT NULL) AS retained_buyers,
    ROUND(
        COUNT(*) FILTER (WHERE cb.customer_id IS NOT NULL)::NUMERIC / NULLIF(COUNT(*), 0),
        4
    ) AS retention_rate
FROM prior_buyers pb
LEFT JOIN current_buyers cb ON cb.customer_id = pb.customer_id;


/* Q24 | Churn Indicators
   Business objective: Flag customers inactive beyond 180 days.
   Business interpretation: Prioritize win-back for high historical value churn risks.
   Why management should care: Churn destroys LTV and inflates acquisition needs. */
SELECT
    lifecycle_status,
    COUNT(*) AS customers,
    ROUND(SUM(lifetime_net_sales), 2) AS historical_sales_at_risk,
    ROUND(AVG(days_since_last_order), 1) AS avg_days_inactive
FROM analytics.vw_customer_360
WHERE lifecycle_status IN ('Churn Risk', 'At Risk')
   OR COALESCE(days_since_last_order, 0) > 90
GROUP BY lifecycle_status
ORDER BY historical_sales_at_risk DESC NULLS LAST;


/* Q25 | Top Customers
   Business objective: Rank highest-value customers by lifetime gross profit.
   Business interpretation: White-glove / loyalty treatment candidates.
   Why management should care: Top decile often contributes outsized profit. */
SELECT
    customer_id,
    customer_number,
    loyalty_tier,
    order_count,
    ROUND(lifetime_gross_profit, 2) AS historical_clv,
    ROUND(lifetime_net_sales, 2) AS lifetime_net_sales,
    ROW_NUMBER() OVER (ORDER BY lifetime_gross_profit DESC NULLS LAST) AS value_rank
FROM analytics.vw_customer_360
WHERE lifetime_gross_profit IS NOT NULL
ORDER BY value_rank
LIMIT 50;


/* Q26 | Dormant Customers
   Business objective: List previously active customers with long inactivity.
   Business interpretation: Win-back campaign targeting list.
   Why management should care: Reactivation can be cheaper than net-new acquisition. */
SELECT
    customer_id,
    customer_number,
    customer_type,
    last_order_date,
    days_since_last_order,
    ROUND(lifetime_net_sales, 2) AS lifetime_net_sales,
    order_count
FROM analytics.vw_customer_360
WHERE days_since_last_order > 180
  AND order_count >= 2
ORDER BY lifetime_net_sales DESC
LIMIT 500;


/* Q27 | Geographic Customer Distribution
   Business objective: Map customers by preferred store region / state.
   Business interpretation: Demand geography for network and media planning.
   Why management should care: Misaligned footprint wastes marketing and inventory. */
SELECT
    r.region_name,
    s.state_code,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(DISTINCT c.customer_id) FILTER (WHERE c.customer_type = 'Loyalty') AS loyalty_customers
FROM oltp.customers c
LEFT JOIN oltp.stores s ON s.store_id = c.preferred_store_id
LEFT JOIN oltp.regions r ON r.region_id = s.region_id
GROUP BY r.region_name, s.state_code
ORDER BY customers DESC;


/* Q28 | Percentile spend distribution
   Business objective: Understand spend concentration via percentiles.
   Business interpretation: p90/p99 show how top-heavy the franchise is.
   Why management should care: Concentration risk and VIP program design. */
SELECT
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY lifetime_net_sales)::NUMERIC, 2) AS p50_sales,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY lifetime_net_sales)::NUMERIC, 2) AS p90_sales,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY lifetime_net_sales)::NUMERIC, 2) AS p99_sales,
    ROUND(AVG(lifetime_net_sales), 2) AS avg_sales
FROM analytics.vw_customer_360
WHERE lifetime_net_sales IS NOT NULL;


-- #############################################################################
-- SECTION C — FINANCE ANALYTICS
-- #############################################################################

/* Q29 | Gross Profit
   Business objective: Calculate gross profit by month.
   Business interpretation: Profit dollars matter more than sales vanity metrics.
   Why management should care: Funds operating expenses and investment capacity. */
SELECT
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(SUM(oi.line_cogs_amount), 2) AS cogs,
    ROUND(SUM(oi.line_net_amount - oi.line_cogs_amount), 2) AS gross_profit
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY 1
ORDER BY 1;


/* Q30 | Profit Margin
   Business objective: Track gross margin % by category and channel.
   Business interpretation: Low-margin mixes erode enterprise profitability.
   Why management should care: Margin is a CFO scorecard metric. */
SELECT
    pcm.category_name,
    ch.channel_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(
        SUM(oi.line_net_amount - oi.line_cogs_amount) / NULLIF(SUM(oi.line_net_amount), 0),
        4
    ) AS gross_margin_pct
FROM oltp.order_items oi
JOIN oltp.orders o ON o.order_id = oi.order_id
JOIN analytics.vw_product_category_map pcm ON pcm.product_id = oi.product_id
JOIN oltp.channels ch ON ch.channel_id = o.channel_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY pcm.category_name, ch.channel_name
ORDER BY gross_margin_pct ASC;


/* Q31 | Discount Analysis
   Business objective: Quantify discount depth and promo dependency.
   Business interpretation: High discount rate may indicate poor full-price sell-through.
   Why management should care: Discounting can destroy margin and brand equity. */
SELECT
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    ROUND(SUM(oi.line_gross_amount), 2) AS gross_sales,
    ROUND(SUM(oi.discount_amount), 2) AS discount_amount,
    ROUND(SUM(oi.discount_amount) / NULLIF(SUM(oi.line_gross_amount), 0), 4) AS discount_rate,
    ROUND(
        SUM(oi.line_net_amount) FILTER (WHERE oi.promotion_id IS NOT NULL)
        / NULLIF(SUM(oi.line_net_amount), 0),
        4
    ) AS promo_sales_mix
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY 1
ORDER BY 1;


/* Q32 | Revenue vs Cost
   Business objective: Bridge net sales to COGS and profit with contribution shares.
   Business interpretation: Visual P&L bridge inputs for finance packs.
   Why management should care: Clarifies whether issues are price, cost, or volume. */
SELECT
    pcm.category_name,
    ROUND(SUM(oi.line_net_amount), 2) AS revenue,
    ROUND(SUM(oi.line_cogs_amount), 2) AS cost,
    ROUND(SUM(oi.line_net_amount - oi.line_cogs_amount), 2) AS profit,
    ROUND(SUM(oi.line_cogs_amount) / NULLIF(SUM(oi.line_net_amount), 0), 4) AS cost_ratio
FROM oltp.order_items oi
JOIN oltp.orders o ON o.order_id = oi.order_id
JOIN analytics.vw_product_category_map pcm ON pcm.product_id = oi.product_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY pcm.category_name
ORDER BY profit DESC;


/* Q33 | Payment Method Analysis
   Business objective: Understand tender mix and value by method.
   Business interpretation: Card/wallet mix affects fees and fraud exposure.
   Why management should care: Treasury and payment-cost optimization. */
SELECT
    method_group,
    method_name,
    payment_month,
    payment_count,
    ROUND(payment_amount, 2) AS payment_amount,
    ROUND(payment_amount / SUM(payment_amount) OVER (PARTITION BY payment_month), 4) AS month_share
FROM analytics.vw_payment_mix
ORDER BY payment_month DESC, payment_amount DESC;


/* Q34 | Monthly Financial Summary
   Business objective: One finance summary table for month-end close support.
   Business interpretation: Compact view of sales, margin, discount, refunds.
   Why management should care: Speeds CFO/controller monthly reviews. */
WITH sales AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        SUM(oi.line_net_amount) AS net_sales,
        SUM(oi.line_cogs_amount) AS cogs,
        SUM(oi.discount_amount) AS discounts,
        COUNT(DISTINCT o.order_id) AS orders
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1
),
refunds AS (
    SELECT
        DATE_TRUNC('month', r.return_date)::DATE AS month_start,
        SUM(ri.quantity_returned * ri.unit_refund_amount) AS refund_amount
    FROM oltp.returns r
    JOIN oltp.return_items ri ON ri.return_id = r.return_id
    GROUP BY 1
)
SELECT
    s.month_start,
    ROUND(s.net_sales, 2) AS net_sales,
    ROUND(s.cogs, 2) AS cogs,
    ROUND(s.net_sales - s.cogs, 2) AS gross_profit,
    ROUND((s.net_sales - s.cogs) / NULLIF(s.net_sales, 0), 4) AS margin_pct,
    ROUND(s.discounts, 2) AS discounts,
    ROUND(COALESCE(r.refund_amount, 0), 2) AS refunds,
    s.orders
FROM sales s
LEFT JOIN refunds r ON r.month_start = s.month_start
ORDER BY s.month_start;


-- #############################################################################
-- SECTION D — OPERATIONS ANALYTICS
-- #############################################################################

/* Q35 | Inventory Turnover (proxy)
   Business objective: Approximate turns as COGS / average inventory value.
   Business interpretation: Low turns = capital trapped; high turns risk stockouts.
   Why management should care: Working-capital efficiency is a board-level topic. */
WITH cogs AS (
    SELECT SUM(oi.line_cogs_amount) AS annualized_cogs
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    WHERE o.order_date >= (SELECT MAX(order_date) - INTERVAL '365 days' FROM oltp.orders)
),
inv AS (
    SELECT AVG(i.quantity_on_hand * p.current_unit_cost) AS avg_inventory_value
    FROM oltp.inventory i
    JOIN oltp.products p ON p.product_id = i.product_id
)
SELECT
    ROUND(c.annualized_cogs, 2) AS cogs_trailing_year,
    ROUND(i.avg_inventory_value, 2) AS avg_inventory_value_proxy,
    ROUND(c.annualized_cogs / NULLIF(i.avg_inventory_value, 0), 2) AS inventory_turnover_proxy
FROM cogs c
CROSS JOIN inv i;


/* Q36 | Stock Coverage (days of supply proxy)
   Business objective: Estimate on-hand coverage vs recent daily demand.
   Business interpretation: Low DOS = stockout risk; high DOS = overbuy.
   Why management should care: Balances service level against inventory cost. */
WITH demand AS (
    SELECT
        oi.product_id,
        SUM(oi.quantity)::NUMERIC / NULLIF(COUNT(DISTINCT o.order_date), 0) AS avg_daily_units
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY oi.product_id
),
stock AS (
    SELECT product_id, SUM(quantity_on_hand) AS on_hand
    FROM oltp.inventory
    GROUP BY product_id
)
SELECT
    p.sku,
    p.product_name,
    s.on_hand,
    ROUND(d.avg_daily_units, 2) AS avg_daily_units,
    ROUND(s.on_hand / NULLIF(d.avg_daily_units, 0), 1) AS days_of_supply
FROM stock s
JOIN demand d ON d.product_id = s.product_id
JOIN oltp.products p ON p.product_id = s.product_id
ORDER BY days_of_supply NULLS LAST
LIMIT 100;


/* Q37 | Stockout Detection
   Business objective: Identify current and historical stockout positions.
   Business interpretation: Zero on-hand for sellable SKUs is lost sales risk.
   Why management should care: Stockouts directly hit revenue and customer trust. */
SELECT
    stock_status,
    location_type,
    COUNT(*) AS positions,
    ROUND(SUM(inventory_value_cost), 2) AS inventory_value
FROM analytics.vw_inventory_health
GROUP BY stock_status, location_type
ORDER BY stock_status, location_type;

-- Historical stockout rate from snapshots
SELECT
    snapshot_date,
    COUNT(*) FILTER (WHERE quantity_on_hand = 0) AS stockout_rows,
    COUNT(*) AS total_rows,
    ROUND(
        COUNT(*) FILTER (WHERE quantity_on_hand = 0)::NUMERIC / NULLIF(COUNT(*), 0),
        4
    ) AS stockout_rate
FROM oltp.inventory_snapshots
GROUP BY snapshot_date
ORDER BY snapshot_date DESC
LIMIT 60;


/* Q38 | Supplier Performance
   Business objective: Score suppliers on fill rate and on-time delivery.
   Business interpretation: Unreliable suppliers drive stockouts and expedites.
   Why management should care: Procurement leverage and dual-sourcing decisions. */
SELECT
    supplier_code,
    supplier_name,
    supplier_tier,
    po_count,
    units_ordered,
    units_received,
    ROUND(fill_rate, 4) AS fill_rate,
    ROUND(on_time_rate::NUMERIC, 4) AS on_time_rate,
    ROUND(avg_actual_lead_time_days::NUMERIC, 1) AS avg_lead_time_days
FROM analytics.vw_supplier_performance
ORDER BY fill_rate ASC NULLS LAST;


/* Q39 | Average Supplier Lead Time
   Business objective: Compare contracted vs actual lead times.
   Business interpretation: Systematic delays require buffer stock or supplier exits.
   Why management should care: Lead-time accuracy underpins replenishment planning. */
SELECT
    supplier_tier,
    ROUND(AVG(contracted_lead_time_days), 1) AS avg_contracted_lead,
    ROUND(AVG(avg_actual_lead_time_days)::NUMERIC, 1) AS avg_actual_lead,
    ROUND(AVG(avg_actual_lead_time_days)::NUMERIC - AVG(contracted_lead_time_days), 1) AS lead_time_variance_days
FROM analytics.vw_supplier_performance
GROUP BY supplier_tier
ORDER BY supplier_tier;


/* Q40 | Store Performance (sales + labor productivity)
   Business objective: Combine sales with labor hours for productivity.
   Business interpretation: Low sales/hour stores need labor or traffic interventions.
   Why management should care: Labor is a major controllable OpEx line. */
WITH store_sales AS (
    SELECT
        o.store_id,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.store_id IS NOT NULL
      AND o.order_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY o.store_id
),
labor AS (
    SELECT store_id, SUM(labor_hours) AS labor_hours
    FROM oltp.store_labor_hours
    WHERE work_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY store_id
)
SELECT
    s.store_code,
    s.store_name,
    r.region_name,
    ROUND(ss.net_sales, 2) AS net_sales_90d,
    ROUND(l.labor_hours, 1) AS labor_hours_90d,
    ROUND(ss.net_sales / NULLIF(l.labor_hours, 0), 2) AS sales_per_labor_hour,
    RANK() OVER (ORDER BY ss.net_sales / NULLIF(l.labor_hours, 0) DESC NULLS LAST) AS productivity_rank
FROM store_sales ss
JOIN oltp.stores s ON s.store_id = ss.store_id
JOIN oltp.regions r ON r.region_id = s.region_id
LEFT JOIN labor l ON l.store_id = ss.store_id
ORDER BY sales_per_labor_hour DESC NULLS LAST;


/* Q41 | Warehouse Performance
   Business objective: Evaluate DC shipment volume and lead times.
   Business interpretation: Slow DCs create online CX issues.
   Why management should care: Fulfillment speed is a digital competitiveness KPI. */
SELECT
    dc_code,
    dc_name,
    COUNT(*) AS shipments,
    ROUND(AVG(fulfillment_lead_time_days)::NUMERIC, 2) AS avg_fulfillment_days,
    ROUND(AVG(transit_days)::NUMERIC, 2) AS avg_transit_days,
    COUNT(*) FILTER (WHERE delay_flag <> 'On Track') AS delayed_shipments,
    ROUND(
        COUNT(*) FILTER (WHERE delay_flag <> 'On Track')::NUMERIC / NULLIF(COUNT(*), 0),
        4
    ) AS delay_rate
FROM analytics.vw_shipment_performance
WHERE dc_code IS NOT NULL
GROUP BY dc_code, dc_name
ORDER BY delay_rate DESC;


/* Q42 | Shipment Delays
   Business objective: Detail delayed shipments for ops exception management.
   Business interpretation: Carrier or DC bottlenecks become visible.
   Why management should care: Delay spikes drive cancellations and NPS damage. */
SELECT
    shipment_id,
    order_id,
    order_date,
    ship_date,
    fulfillment_lead_time_days,
    carrier_name,
    delay_flag,
    dc_name
FROM analytics.vw_shipment_performance
WHERE delay_flag IN ('Delayed Ship', 'Delayed Delivery')
ORDER BY fulfillment_lead_time_days DESC NULLS LAST
LIMIT 200;


/* Q43 | Return Rate
   Business objective: Compute return rate by category and channel.
   Business interpretation: High return categories need sizing/quality/content fixes.
   Why management should care: Returns destroy margin and logistics capacity. */
WITH sold AS (
    SELECT
        pcm.category_name,
        ch.channel_name,
        SUM(oi.quantity) AS units_sold,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.order_items oi
    JOIN oltp.orders o ON o.order_id = oi.order_id
    JOIN analytics.vw_product_category_map pcm ON pcm.product_id = oi.product_id
    JOIN oltp.channels ch ON ch.channel_id = o.channel_id
    GROUP BY pcm.category_name, ch.channel_name
),
ret AS (
    SELECT
        pcm.category_name,
        ch.channel_name,
        SUM(f.quantity_returned) AS units_returned,
        SUM(f.refund_line_amount) AS refund_amount
    FROM analytics.vw_fact_return_line f
    JOIN analytics.vw_product_category_map pcm ON pcm.product_id = f.product_id
    JOIN oltp.channels ch ON ch.channel_id = f.channel_id
    GROUP BY pcm.category_name, ch.channel_name
)
SELECT
    s.category_name,
    s.channel_name,
    ROUND(r.units_returned::NUMERIC / NULLIF(s.units_sold, 0), 4) AS return_rate_units,
    ROUND(r.refund_amount / NULLIF(s.net_sales, 0), 4) AS return_rate_value
FROM sold s
LEFT JOIN ret r
  ON r.category_name = s.category_name
 AND r.channel_name = s.channel_name
ORDER BY return_rate_value DESC NULLS LAST;


/* Q44 | Return Cost
   Business objective: Quantify refund cost and restock outcomes by reason.
   Business interpretation: Defect vs change-mind mix guides quality vs CX actions.
   Why management should care: Return cost is often under-managed profit leakage. */
SELECT
    return_reason_code,
    COUNT(*) AS return_lines,
    SUM(quantity_returned) AS units_returned,
    ROUND(SUM(refund_line_amount), 2) AS refund_cost,
    ROUND(AVG(CASE WHEN restock_flag THEN 1.0 ELSE 0.0 END), 4) AS restock_rate
FROM analytics.vw_fact_return_line
GROUP BY return_reason_code
ORDER BY refund_cost DESC;


-- #############################################################################
-- SECTION E — MARKETING ANALYTICS
-- #############################################################################

/* Q45 | Campaign ROI
   Business objective: Rank campaigns by ROI ((gross profit - spend) / spend).
   Business interpretation: Scale winners; cut or redesign negative-ROI campaigns.
   Why management should care: Marketing budget accountability. */
SELECT
    campaign_code,
    campaign_name,
    campaign_type,
    ROUND(actual_spend, 2) AS actual_spend,
    ROUND(order_gross_profit, 2) AS order_gross_profit,
    ROUND(campaign_roi, 4) AS campaign_roi,
    attributed_orders,
    conversion_rate
FROM analytics.vw_campaign_performance
WHERE actual_spend > 0
ORDER BY campaign_roi DESC NULLS LAST;


/* Q46 | Conversion Rate
   Business objective: Measure convert / sent (and click-through style rates).
   Business interpretation: Low conversion with high spend wastes media dollars.
   Why management should care: Creative and targeting quality indicator. */
SELECT
    campaign_type,
    SUM(sent_count) AS sent_count,
    SUM(open_count) AS open_count,
    SUM(click_count) AS click_count,
    SUM(convert_count) AS convert_count,
    ROUND(SUM(convert_count)::NUMERIC / NULLIF(SUM(sent_count), 0), 4) AS conversion_rate,
    ROUND(SUM(click_count)::NUMERIC / NULLIF(SUM(open_count), 0), 4) AS click_to_open_rate
FROM analytics.vw_campaign_performance
GROUP BY campaign_type
ORDER BY conversion_rate DESC NULLS LAST;


/* Q47 | Revenue by Campaign
   Business objective: Attribute net sales to campaigns.
   Business interpretation: Identifies revenue-producing flights vs awareness-only.
   Why management should care: Ties marketing activity to commercial outcomes. */
SELECT
    campaign_code,
    campaign_name,
    objective_code,
    ROUND(order_net_sales, 2) AS attributed_net_sales,
    attributed_orders,
    attributed_customers,
    ROUND(order_net_sales / NULLIF(attributed_orders, 0), 2) AS aov_on_attributed_orders
FROM analytics.vw_campaign_performance
ORDER BY order_net_sales DESC;


/* Q48 | Campaign Performance by Region
   Business objective: See where campaign-attributed orders concentrate geographically.
   Business interpretation: Regional creative/offer fit differences.
   Why management should care: Avoids one-size-fits-all national campaigns. */
SELECT
    mc.campaign_code,
    r.region_name,
    COUNT(DISTINCT o.order_id) AS attributed_orders,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales
FROM oltp.orders o
JOIN oltp.order_items oi ON oi.order_id = o.order_id
JOIN oltp.marketing_campaigns mc ON mc.campaign_id = o.campaign_id
LEFT JOIN oltp.stores s ON s.store_id = o.store_id
LEFT JOIN oltp.regions r ON r.region_id = s.region_id
WHERE o.campaign_id IS NOT NULL
GROUP BY mc.campaign_code, r.region_name
ORDER BY mc.campaign_code, net_sales DESC;


/* Q49 | Customer Acquisition by Campaign
   Business objective: Count first-time buyers attributed to campaigns.
   Business interpretation: Separates acquisition vs retention campaign effectiveness.
   Why management should care: CAC and growth engine measurement. */
WITH first_orders AS (
    SELECT customer_id, MIN(order_id) AS first_order_id
    FROM oltp.orders
    WHERE order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY customer_id
)
SELECT
    mc.campaign_code,
    mc.campaign_name,
    mc.objective_code,
    COUNT(*) AS new_customers_acquired
FROM first_orders f
JOIN oltp.orders o ON o.order_id = f.first_order_id
JOIN oltp.marketing_campaigns mc ON mc.campaign_id = o.campaign_id
WHERE o.campaign_id IS NOT NULL
GROUP BY mc.campaign_code, mc.campaign_name, mc.objective_code
ORDER BY new_customers_acquired DESC;


-- #############################################################################
-- SECTION F — EXECUTIVE KPIs
-- #############################################################################

/* Q50 | Executive Scorecard (latest 30 days vs prior 30)
   Business objective: One-screen health check for ExCo.
   Business interpretation: Directional movement across sales, margin, customers, ops.
   Why management should care: Compresses decision latency for leadership. */
SELECT * FROM analytics.fn_executive_scorecard(
    (CURRENT_DATE - INTERVAL '30 days')::DATE,
    CURRENT_DATE
);


/* Q51 | Top Risks
   Business objective: Surface quantified risk signals for leadership attention.
   Business interpretation: Ranked issues by estimated commercial exposure.
   Why management should care: Forces prioritization instead of anecdote-driven firefighting. */
WITH risks AS (
    SELECT 'High churn-risk customer sales' AS risk_name,
           ROUND(SUM(lifetime_net_sales), 2) AS exposure_amount,
           'Customer' AS domain
    FROM analytics.vw_customer_360
    WHERE lifecycle_status = 'Churn Risk'
    UNION ALL
    SELECT 'Stockout inventory positions',
           COUNT(*)::NUMERIC,
           'Operations'
    FROM analytics.vw_inventory_health
    WHERE stock_status = 'Stockout'
    UNION ALL
    SELECT 'Negative/low ROI campaigns (count)',
           COUNT(*)::NUMERIC,
           'Marketing'
    FROM analytics.vw_campaign_performance
    WHERE campaign_roi IS NOT NULL AND campaign_roi < 0
    UNION ALL
    SELECT 'Delayed shipments (90d)',
           COUNT(*)::NUMERIC,
           'Operations'
    FROM analytics.vw_shipment_performance
    WHERE delay_flag <> 'On Track'
      AND order_date >= CURRENT_DATE - INTERVAL '90 days'
)
SELECT
    risk_name,
    domain,
    exposure_amount,
    RANK() OVER (ORDER BY exposure_amount DESC) AS risk_rank
FROM risks
ORDER BY risk_rank;


/* Q52 | Best Opportunities
   Business objective: Highlight upside levers with evidence.
   Business interpretation: Where incremental effort yields outsized return.
   Why management should care: Balances risk review with growth agenda. */
WITH opps AS (
    SELECT 'Champions customers expand' AS opportunity,
           COUNT(*)::NUMERIC AS magnitude,
           ROUND(SUM(lifetime_net_sales), 2) AS value_signal
    FROM analytics.vw_customer_rfm
    WHERE rfm_segment = 'Champions'
    UNION ALL
    SELECT 'Top ROI campaigns to scale',
           COUNT(*)::NUMERIC,
           ROUND(SUM(order_gross_profit), 2)
    FROM analytics.vw_campaign_performance
    WHERE campaign_roi >= 1
    UNION ALL
    SELECT 'Below-reorder SKUs to replenish',
           COUNT(*)::NUMERIC,
           ROUND(SUM(inventory_value_cost), 2)
    FROM analytics.vw_inventory_health
    WHERE stock_status = 'Below Reorder'
)
SELECT *
FROM opps
ORDER BY value_signal DESC NULLS LAST;


/* Q53 | KPI Summary Dashboard Query
   Business objective: Provide a tidy KPI key-value feed for dashboards.
   Business interpretation: Canonical KPI set for Power BI cards.
   Why management should care: Single definition reduces metric debates. */
WITH sales_30 AS (
    SELECT
        SUM(net_sales) AS net_sales,
        SUM(gross_profit) AS gross_profit,
        SUM(order_count) AS orders
    FROM analytics.vw_sales_daily
    WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
),
cust AS (
    SELECT
        COUNT(*) FILTER (WHERE lifecycle_status = 'Active') AS active_customers,
        COUNT(*) FILTER (WHERE lifecycle_status = 'Churn Risk') AS churn_risk_customers
    FROM analytics.vw_customer_360
),
ops AS (
    SELECT COUNT(*) FILTER (WHERE stock_status = 'Stockout') AS stockouts
    FROM analytics.vw_inventory_health
)
SELECT * FROM (
    SELECT 'net_sales_30d' AS kpi, ROUND(net_sales, 2)::TEXT AS kpi_value FROM sales_30
    UNION ALL
    SELECT 'gross_profit_30d', ROUND(gross_profit, 2)::TEXT FROM sales_30
    UNION ALL
    SELECT 'margin_pct_30d',
           ROUND(gross_profit / NULLIF(net_sales, 0), 4)::TEXT FROM sales_30
    UNION ALL
    SELECT 'orders_30d', orders::TEXT FROM sales_30
    UNION ALL
    SELECT 'aov_30d', ROUND(net_sales / NULLIF(orders, 0), 2)::TEXT FROM sales_30
    UNION ALL
    SELECT 'active_customers', active_customers::TEXT FROM cust
    UNION ALL
    SELECT 'churn_risk_customers', churn_risk_customers::TEXT FROM cust
    UNION ALL
    SELECT 'stockout_positions', stockouts::TEXT FROM ops
) k
ORDER BY kpi;


/* Q54 | Recursive category hierarchy walk
   Business objective: Expand category tree from L1 roots to descendants.
   Business interpretation: Validates hierarchy completeness for merchandising rollups.
   Why management should care: Broken hierarchies corrupt every category KPI. */
WITH RECURSIVE cat_tree AS (
    SELECT
        category_id,
        category_code,
        category_name,
        parent_category_id,
        category_level,
        category_code::TEXT AS path
    FROM oltp.product_categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT
        c.category_id,
        c.category_code,
        c.category_name,
        c.parent_category_id,
        c.category_level,
        ct.path || ' > ' || c.category_code
    FROM oltp.product_categories c
    JOIN cat_tree ct ON ct.category_id = c.parent_category_id
)
SELECT *
FROM cat_tree
ORDER BY path;


/* Q55 | Same-store sales growth proxy
   Business objective: YoY sales for stores open >= 13 months before period.
   Business interpretation: Underlying demand excluding new-store openings.
   Why management should care: Board-level comparable sales metric. */
WITH eligible_stores AS (
    SELECT store_id
    FROM oltp.stores
    WHERE open_date <= (CURRENT_DATE - INTERVAL '13 months')
      AND is_active = TRUE
),
monthly_store AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        o.store_id,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    JOIN eligible_stores e ON e.store_id = o.store_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1, 2
)
SELECT
    month_start,
    ROUND(SUM(net_sales), 2) AS sss_net_sales,
    ROUND(
        (SUM(net_sales) - LAG(SUM(net_sales), 12) OVER (ORDER BY month_start))
        / NULLIF(LAG(SUM(net_sales), 12) OVER (ORDER BY month_start), 0),
        4
    ) AS sss_yoy_growth_pct
FROM monthly_store
GROUP BY month_start
ORDER BY month_start;


/* Q56 | Channel mix trend with moving average
   Business objective: Track digital vs physical mix with 3-month moving average.
   Business interpretation: Omnichannel transformation progress.
   Why management should care: Channel shift changes cost-to-serve and CX model. */
WITH monthly_channel AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        ch.channel_group,
        SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    JOIN oltp.channels ch ON ch.channel_id = o.channel_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY 1, 2
),
share AS (
    SELECT
        month_start,
        channel_group,
        net_sales,
        net_sales / SUM(net_sales) OVER (PARTITION BY month_start) AS mix_pct
    FROM monthly_channel
)
SELECT
    month_start,
    channel_group,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(mix_pct, 4) AS mix_pct,
    ROUND(AVG(mix_pct) OVER (
        PARTITION BY channel_group
        ORDER BY month_start
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 4) AS mix_pct_ma3
FROM share
ORDER BY month_start, channel_group;


-- End of business_queries.sql (56 queries)
