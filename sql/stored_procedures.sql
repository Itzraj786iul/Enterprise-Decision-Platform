-- =============================================================================
-- Enterprise Business Analytics & Decision Intelligence Platform
-- PostgreSQL Functions (stored procedures / RPCs)
-- =============================================================================
-- Parameterized, reusable analytics routines for reporting & app layers.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics, oltp, public;

-- -----------------------------------------------------------------------------
-- 1) Monthly revenue for a date window
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION analytics.fn_monthly_revenue(
    p_start_date DATE DEFAULT NULL,
    p_end_date   DATE DEFAULT NULL
)
RETURNS TABLE (
    year_number     INTEGER,
    month_number    INTEGER,
    month_start     DATE,
    net_sales       NUMERIC,
    gross_profit    NUMERIC,
    order_count     BIGINT,
    yoy_net_sales   NUMERIC,
    yoy_growth_pct  NUMERIC
)
LANGUAGE sql
STABLE
AS $$
WITH bounds AS (
    SELECT
        COALESCE(p_start_date, (SELECT MIN(order_date) FROM oltp.orders)) AS start_dt,
        COALESCE(p_end_date, (SELECT MAX(order_date) FROM oltp.orders)) AS end_dt
),
monthly AS (
    SELECT
        d.year_number,
        d.month_number,
        DATE_TRUNC('month', f.order_date)::DATE AS month_start,
        SUM(f.line_net_amount) AS net_sales,
        SUM(f.line_net_amount - f.line_cogs_amount) AS gross_profit,
        COUNT(DISTINCT f.order_id) AS order_count
    FROM oltp.order_items oi
    JOIN oltp.orders f
        ON f.order_id = oi.order_id
    JOIN oltp.calendar_date d
        ON d.full_date = f.order_date
    CROSS JOIN bounds b
    WHERE f.order_date BETWEEN b.start_dt AND b.end_dt
      AND f.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY d.year_number, d.month_number, DATE_TRUNC('month', f.order_date)::DATE
)
SELECT
    m.year_number,
    m.month_number,
    m.month_start,
    ROUND(m.net_sales, 2),
    ROUND(m.gross_profit, 2),
    m.order_count,
    ROUND(LAG(m.net_sales, 12) OVER (ORDER BY m.month_start), 2) AS yoy_net_sales,
    ROUND(
        (m.net_sales - LAG(m.net_sales, 12) OVER (ORDER BY m.month_start))
        / NULLIF(LAG(m.net_sales, 12) OVER (ORDER BY m.month_start), 0),
        4
    ) AS yoy_growth_pct
FROM monthly m
ORDER BY m.month_start;
$$;

-- -----------------------------------------------------------------------------
-- 2) Store performance scorecard for a period
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION analytics.fn_store_performance(
    p_start_date DATE,
    p_end_date   DATE
)
RETURNS TABLE (
    store_id            INTEGER,
    store_code          VARCHAR,
    store_name          VARCHAR,
    region_name         VARCHAR,
    net_sales           NUMERIC,
    gross_profit        NUMERIC,
    margin_pct          NUMERIC,
    order_count         BIGINT,
    aov                 NUMERIC,
    units_sold          NUMERIC,
    sales_rank          BIGINT,
    sales_per_sqft      NUMERIC
)
LANGUAGE sql
STABLE
AS $$
SELECT
    s.store_id,
    s.store_code,
    s.store_name,
    r.region_name,
    ROUND(SUM(oi.line_net_amount), 2) AS net_sales,
    ROUND(SUM(oi.line_net_amount - oi.line_cogs_amount), 2) AS gross_profit,
    ROUND(
        SUM(oi.line_net_amount - oi.line_cogs_amount) / NULLIF(SUM(oi.line_net_amount), 0),
        4
    ) AS margin_pct,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(oi.line_net_amount) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov,
    SUM(oi.quantity)::NUMERIC AS units_sold,
    RANK() OVER (ORDER BY SUM(oi.line_net_amount) DESC) AS sales_rank,
    ROUND(SUM(oi.line_net_amount) / NULLIF(s.selling_sq_ft, 0), 2) AS sales_per_sqft
FROM oltp.orders o
JOIN oltp.order_items oi
    ON oi.order_id = o.order_id
JOIN oltp.stores s
    ON s.store_id = o.store_id
JOIN oltp.regions r
    ON r.region_id = s.region_id
WHERE o.order_date BETWEEN p_start_date AND p_end_date
  AND o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY s.store_id, s.store_code, s.store_name, r.region_name, s.selling_sq_ft
ORDER BY net_sales DESC;
$$;

-- -----------------------------------------------------------------------------
-- 3) Customer RFM snapshot as-of a date
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION analytics.fn_customer_rfm_asof(
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    customer_id         BIGINT,
    recency_days        INTEGER,
    frequency           BIGINT,
    monetary            NUMERIC,
    r_score             INTEGER,
    f_score             INTEGER,
    m_score             INTEGER,
    rfm_segment         TEXT
)
LANGUAGE sql
STABLE
AS $$
WITH cust AS (
    SELECT
        o.customer_id,
        (p_as_of_date - MAX(o.order_date))::INTEGER AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.line_net_amount) AS monetary
    FROM oltp.orders o
    JOIN oltp.order_items oi
        ON oi.order_id = o.order_id
    WHERE o.order_date <= p_as_of_date
      AND o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY o.customer_id
),
scored AS (
    SELECT
        c.*,
        NTILE(5) OVER (ORDER BY recency_days DESC)::INTEGER AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)::INTEGER AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)::INTEGER AS m_score
    FROM cust c
)
SELECT
    customer_id,
    recency_days,
    frequency,
    ROUND(monetary, 2),
    r_score,
    f_score,
    m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising New'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk Loyal'
        WHEN r_score <= 2 AND m_score <= 2 THEN 'Hibernating'
        ELSE 'Need Attention'
    END AS rfm_segment
FROM scored;
$$;

-- -----------------------------------------------------------------------------
-- 4) Category sales with contribution and rank for a period
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION analytics.fn_category_contribution(
    p_start_date DATE,
    p_end_date   DATE
)
RETURNS TABLE (
    category_code       VARCHAR,
    category_name       VARCHAR,
    net_sales           NUMERIC,
    gross_profit        NUMERIC,
    units_sold          NUMERIC,
    contribution_pct    NUMERIC,
    sales_rank          BIGINT,
    cumulative_pct      NUMERIC
)
LANGUAGE sql
STABLE
AS $$
WITH cat_sales AS (
    SELECT
        pcm.category_code,
        pcm.category_name,
        SUM(oi.line_net_amount) AS net_sales,
        SUM(oi.line_net_amount - oi.line_cogs_amount) AS gross_profit,
        SUM(oi.quantity)::NUMERIC AS units_sold
    FROM oltp.order_items oi
    JOIN oltp.orders o
        ON o.order_id = oi.order_id
    JOIN analytics.vw_product_category_map pcm
        ON pcm.product_id = oi.product_id
    WHERE o.order_date BETWEEN p_start_date AND p_end_date
      AND o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY pcm.category_code, pcm.category_name
),
tot AS (
    SELECT SUM(net_sales) AS total_sales FROM cat_sales
)
SELECT
    c.category_code,
    c.category_name,
    ROUND(c.net_sales, 2),
    ROUND(c.gross_profit, 2),
    c.units_sold,
    ROUND(c.net_sales / NULLIF(t.total_sales, 0), 4) AS contribution_pct,
    RANK() OVER (ORDER BY c.net_sales DESC) AS sales_rank,
    ROUND(
        SUM(c.net_sales) OVER (ORDER BY c.net_sales DESC)
        / NULLIF(t.total_sales, 0),
        4
    ) AS cumulative_pct
FROM cat_sales c
CROSS JOIN tot t
ORDER BY c.net_sales DESC;
$$;

-- -----------------------------------------------------------------------------
-- 5) Executive KPI snapshot for a period (single-row scorecard)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION analytics.fn_executive_scorecard(
    p_start_date DATE,
    p_end_date   DATE
)
RETURNS TABLE (
    net_sales               NUMERIC,
    prior_period_net_sales  NUMERIC,
    sales_growth_pct        NUMERIC,
    gross_profit            NUMERIC,
    margin_pct              NUMERIC,
    order_count             BIGINT,
    aov                     NUMERIC,
    active_customers        BIGINT,
    return_rate_value       NUMERIC,
    avg_fulfillment_days    NUMERIC
)
LANGUAGE sql
STABLE
AS $$
WITH period_len AS (
    SELECT (p_end_date - p_start_date) AS days
),
cur AS (
    SELECT
        SUM(oi.line_net_amount) AS net_sales,
        SUM(oi.line_net_amount - oi.line_cogs_amount) AS gross_profit,
        COUNT(DISTINCT o.order_id) AS order_count,
        COUNT(DISTINCT o.customer_id) AS active_customers
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_date BETWEEN p_start_date AND p_end_date
      AND o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
),
prior AS (
    SELECT SUM(oi.line_net_amount) AS net_sales
    FROM oltp.orders o
    JOIN oltp.order_items oi ON oi.order_id = o.order_id
    CROSS JOIN period_len pl
    WHERE o.order_date BETWEEN (p_start_date - (pl.days + 1)) AND (p_start_date - 1)
      AND o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
),
rets AS (
    SELECT COALESCE(SUM(ri.quantity_returned * ri.unit_refund_amount), 0) AS refund_amt
    FROM oltp.returns r
    JOIN oltp.return_items ri ON ri.return_id = r.return_id
    WHERE r.return_date BETWEEN p_start_date AND p_end_date
),
ship AS (
    SELECT AVG((sh.ship_date - o.order_date)) AS avg_lead
    FROM oltp.shipments sh
    JOIN oltp.orders o ON o.order_id = sh.order_id
    WHERE o.order_date BETWEEN p_start_date AND p_end_date
      AND sh.ship_date IS NOT NULL
)
SELECT
    ROUND(c.net_sales, 2),
    ROUND(p.net_sales, 2),
    ROUND((c.net_sales - p.net_sales) / NULLIF(p.net_sales, 0), 4),
    ROUND(c.gross_profit, 2),
    ROUND(c.gross_profit / NULLIF(c.net_sales, 0), 4),
    c.order_count,
    ROUND(c.net_sales / NULLIF(c.order_count, 0), 2),
    c.active_customers,
    ROUND(r.refund_amt / NULLIF(c.net_sales, 0), 4),
    ROUND(s.avg_lead::NUMERIC, 2)
FROM cur c
CROSS JOIN prior p
CROSS JOIN rets r
CROSS JOIN ship s;
$$;

-- -----------------------------------------------------------------------------
-- 6) Refresh helper note: materialize heavy marts (optional pattern)
-- -----------------------------------------------------------------------------
-- Example usage pattern for future materialized views:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_sales_daily;
-- Create MVs in a later performance phase if BI latency requires it.

COMMENT ON FUNCTION analytics.fn_monthly_revenue IS
'Monthly net sales with YoY lag comparison for steering packs.';
COMMENT ON FUNCTION analytics.fn_store_performance IS
'Store league table with rank and sales productivity for a date window.';
COMMENT ON FUNCTION analytics.fn_customer_rfm_asof IS
'Point-in-time RFM segmentation for CRM campaigns.';
COMMENT ON FUNCTION analytics.fn_category_contribution IS
'Category contribution and cumulative share (Pareto) for merchandising.';
COMMENT ON FUNCTION analytics.fn_executive_scorecard IS
'Single-row executive KPI snapshot vs prior equal-length period.';
