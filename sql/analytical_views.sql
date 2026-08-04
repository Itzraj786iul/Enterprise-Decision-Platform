-- =============================================================================
-- Enterprise Business Analytics & Decision Intelligence Platform
-- Analytical Views for Power BI / Streamlit / SQL consumers
-- =============================================================================
-- Apply after database/schema.sql (+ optional database/views.sql).
-- These views encapsulate KPI grains so BI tools avoid reinventing joins.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics, oltp, public;

-- -----------------------------------------------------------------------------
-- Helper: product with L1 category (products typically hang off L2 nodes)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_product_category_map AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    p.brand_name,
    p.is_active,
    p.current_list_price,
    p.current_unit_cost,
    p.primary_supplier_id,
    c2.category_id          AS subcategory_id,
    c2.category_code        AS subcategory_code,
    c2.category_name        AS subcategory_name,
    c1.category_id          AS category_id,
    c1.category_code        AS category_code,
    c1.category_name        AS category_name
FROM oltp.products p
JOIN oltp.product_categories c2
    ON c2.category_id = p.category_id
LEFT JOIN oltp.product_categories c1
    ON c1.category_id = c2.parent_category_id;

-- -----------------------------------------------------------------------------
-- Sales line fact (primary commercial grain)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_fact_sales_line AS
SELECT
    oi.order_item_id,
    oi.order_id,
    o.order_number,
    o.order_date,
    o.order_timestamp,
    o.order_status,
    o.customer_id,
    o.store_id,
    o.channel_id,
    o.campaign_id,
    o.employee_id,
    oi.product_id,
    oi.line_number,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.discount_amount,
    oi.line_gross_amount,
    oi.line_net_amount,
    oi.line_cogs_amount,
    (oi.line_net_amount - oi.line_cogs_amount) AS line_gross_profit,
    CASE
        WHEN oi.line_net_amount = 0 THEN NULL
        ELSE ROUND((oi.line_net_amount - oi.line_cogs_amount) / oi.line_net_amount, 4)
    END AS line_margin_pct,
    oi.promotion_id,
    oi.is_gift,
    d.year_number,
    d.quarter_number,
    d.month_number,
    d.month_name,
    d.week_of_year,
    d.season_name,
    d.is_weekend,
    d.is_holiday
FROM oltp.order_items oi
JOIN oltp.orders o
    ON o.order_id = oi.order_id
JOIN oltp.calendar_date d
    ON d.full_date = o.order_date
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned');

-- -----------------------------------------------------------------------------
-- Daily sales by store / channel (Power BI friendly)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_sales_daily AS
SELECT
    f.order_date,
    f.year_number,
    f.quarter_number,
    f.month_number,
    f.store_id,
    s.store_code,
    s.store_name,
    s.store_format,
    s.region_id,
    r.region_code,
    r.region_name,
    f.channel_id,
    ch.channel_code,
    ch.channel_name,
    COUNT(DISTINCT f.order_id)              AS order_count,
    SUM(f.quantity)                         AS units_sold,
    SUM(f.line_gross_amount)                AS gross_sales,
    SUM(f.discount_amount)                  AS discount_amount,
    SUM(f.line_net_amount)                  AS net_sales,
    SUM(f.line_cogs_amount)                 AS cogs_amount,
    SUM(f.line_gross_profit)                AS gross_profit
FROM analytics.vw_fact_sales_line f
LEFT JOIN oltp.stores s
    ON s.store_id = f.store_id
LEFT JOIN oltp.regions r
    ON r.region_id = s.region_id
JOIN oltp.channels ch
    ON ch.channel_id = f.channel_id
GROUP BY
    f.order_date, f.year_number, f.quarter_number, f.month_number,
    f.store_id, s.store_code, s.store_name, s.store_format,
    s.region_id, r.region_code, r.region_name,
    f.channel_id, ch.channel_code, ch.channel_name;

-- -----------------------------------------------------------------------------
-- Monthly sales mart
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_sales_monthly AS
SELECT
    year_number,
    month_number,
    DATE_TRUNC('month', order_date)::DATE AS month_start,
    SUM(net_sales)      AS net_sales,
    SUM(gross_sales)    AS gross_sales,
    SUM(cogs_amount)    AS cogs_amount,
    SUM(gross_profit)   AS gross_profit,
    SUM(discount_amount) AS discount_amount,
    SUM(order_count)    AS order_count,
    SUM(units_sold)     AS units_sold
FROM analytics.vw_sales_daily
GROUP BY year_number, month_number, DATE_TRUNC('month', order_date)::DATE;

-- -----------------------------------------------------------------------------
-- Customer 360 base
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_customer_360 AS
WITH order_stats AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id)                      AS order_count,
        MIN(o.order_date)                               AS first_order_date,
        MAX(o.order_date)                               AS last_order_date,
        SUM(oi.line_net_amount)                         AS lifetime_net_sales,
        SUM(oi.line_net_amount - oi.line_cogs_amount)   AS lifetime_gross_profit,
        SUM(oi.quantity)                                AS lifetime_units,
        AVG(o.net_amount)                               AS avg_order_value
    FROM oltp.orders o
    JOIN oltp.order_items oi
        ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
    GROUP BY o.customer_id
)
SELECT
    c.customer_id,
    c.customer_number,
    c.customer_type,
    c.registration_date,
    c.preferred_store_id,
    c.is_active,
    la.tier_code                    AS loyalty_tier,
    la.points_balance,
    os.order_count,
    os.first_order_date,
    os.last_order_date,
    os.lifetime_net_sales,
    os.lifetime_gross_profit,
    os.lifetime_units,
    os.avg_order_value,
    (CURRENT_DATE - os.last_order_date) AS days_since_last_order,
    CASE
        WHEN os.last_order_date IS NULL THEN 'Never Purchased'
        WHEN (CURRENT_DATE - os.last_order_date) > 180 THEN 'Churn Risk'
        WHEN (CURRENT_DATE - os.last_order_date) > 90 THEN 'At Risk'
        WHEN os.order_count = 1 THEN 'One-Time'
        ELSE 'Active'
    END AS lifecycle_status
FROM oltp.customers c
LEFT JOIN oltp.loyalty_accounts la
    ON la.customer_id = c.customer_id
LEFT JOIN order_stats os
    ON os.customer_id = c.customer_id;

-- -----------------------------------------------------------------------------
-- RFM scoring view (as-of latest order activity in data)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_customer_rfm AS
WITH base AS (
    SELECT
        customer_id,
        last_order_date,
        order_count,
        lifetime_net_sales,
        days_since_last_order
    FROM analytics.vw_customer_360
    WHERE order_count IS NOT NULL
),
scored AS (
    SELECT
        b.*,
        -- High R = more recent (few days since last order)
        NTILE(5) OVER (ORDER BY days_since_last_order DESC) AS r_score,
        NTILE(5) OVER (ORDER BY order_count ASC) AS f_score,
        NTILE(5) OVER (ORDER BY lifetime_net_sales ASC) AS m_score
    FROM base b
)
SELECT
    customer_id,
    last_order_date,
    order_count,
    lifetime_net_sales,
    days_since_last_order,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising New'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk Loyal'
        WHEN r_score <= 2 AND m_score <= 2 THEN 'Hibernating'
        ELSE 'Need Attention'
    END AS rfm_segment
FROM scored;

-- -----------------------------------------------------------------------------
-- Inventory health
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_inventory_health AS
SELECT
    i.inventory_id,
    i.product_id,
    pcm.sku,
    pcm.product_name,
    pcm.category_name,
    i.location_type,
    i.store_id,
    s.store_name,
    i.dc_id,
    dc.dc_name,
    i.quantity_on_hand,
    i.quantity_reserved,
    i.quantity_available,
    i.reorder_point,
    i.max_stock,
    i.quantity_on_hand * p.current_unit_cost AS inventory_value_cost,
    CASE
        WHEN i.quantity_on_hand = 0 THEN 'Stockout'
        WHEN i.reorder_point IS NOT NULL AND i.quantity_on_hand <= i.reorder_point THEN 'Below Reorder'
        WHEN i.max_stock IS NOT NULL AND i.quantity_on_hand >= i.max_stock THEN 'Overstock'
        ELSE 'Healthy'
    END AS stock_status
FROM oltp.inventory i
JOIN oltp.products p
    ON p.product_id = i.product_id
LEFT JOIN analytics.vw_product_category_map pcm
    ON pcm.product_id = i.product_id
LEFT JOIN oltp.stores s
    ON s.store_id = i.store_id
LEFT JOIN oltp.distribution_centers dc
    ON dc.dc_id = i.dc_id;

-- -----------------------------------------------------------------------------
-- Returns fact
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_fact_return_line AS
SELECT
    ri.return_item_id,
    ri.return_id,
    r.return_date,
    r.order_id,
    r.customer_id,
    r.return_status,
    ri.order_item_id,
    ri.product_id,
    ri.quantity_returned,
    ri.unit_refund_amount,
    (ri.quantity_returned * ri.unit_refund_amount) AS refund_line_amount,
    ri.restock_flag,
    ri.return_reason_code,
    o.order_date,
    o.store_id,
    o.channel_id,
    (r.return_date - o.order_date) AS days_to_return
FROM oltp.return_items ri
JOIN oltp.returns r
    ON r.return_id = ri.return_id
JOIN oltp.orders o
    ON o.order_id = r.order_id;

-- -----------------------------------------------------------------------------
-- Supplier performance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_supplier_performance AS
SELECT
    po.supplier_id,
    s.supplier_code,
    s.supplier_name,
    s.supplier_tier,
    s.lead_time_days_avg AS contracted_lead_time_days,
    s.reliability_score,
    COUNT(DISTINCT po.purchase_order_id) AS po_count,
    SUM(poi.quantity_ordered) AS units_ordered,
    COALESCE(SUM(gri.quantity_received), 0) AS units_received,
    CASE
        WHEN SUM(poi.quantity_ordered) = 0 THEN NULL
        ELSE ROUND(COALESCE(SUM(gri.quantity_received), 0)::NUMERIC / SUM(poi.quantity_ordered), 4)
    END AS fill_rate,
    AVG(CASE WHEN gr.is_on_time THEN 1.0 ELSE 0.0 END) AS on_time_rate,
    AVG((gr.receipt_date - po.order_date)) AS avg_actual_lead_time_days
FROM oltp.purchase_orders po
JOIN oltp.suppliers s
    ON s.supplier_id = po.supplier_id
JOIN oltp.purchase_order_items poi
    ON poi.purchase_order_id = po.purchase_order_id
LEFT JOIN oltp.goods_receipts gr
    ON gr.purchase_order_id = po.purchase_order_id
LEFT JOIN oltp.goods_receipt_items gri
    ON gri.receipt_id = gr.receipt_id
   AND gri.po_item_id = poi.po_item_id
GROUP BY
    po.supplier_id, s.supplier_code, s.supplier_name, s.supplier_tier,
    s.lead_time_days_avg, s.reliability_score;

-- -----------------------------------------------------------------------------
-- Campaign performance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_campaign_performance AS
WITH spend AS (
    SELECT
        campaign_id,
        campaign_code,
        campaign_name,
        campaign_type,
        start_date,
        end_date,
        budget_amount,
        actual_spend,
        objective_code,
        status_code
    FROM oltp.marketing_campaigns
),
responses AS (
    SELECT
        campaign_id,
        COUNT(*) FILTER (WHERE response_type = 'Sent') AS sent_count,
        COUNT(*) FILTER (WHERE response_type = 'Open') AS open_count,
        COUNT(*) FILTER (WHERE response_type = 'Click') AS click_count,
        COUNT(*) FILTER (WHERE response_type = 'Convert') AS convert_count,
        COALESCE(SUM(attributed_revenue) FILTER (WHERE response_type = 'Convert'), 0) AS attributed_revenue
    FROM oltp.campaign_responses
    GROUP BY campaign_id
),
order_attr AS (
    SELECT
        o.campaign_id,
        SUM(oi.line_net_amount) AS order_net_sales,
        SUM(oi.line_net_amount - oi.line_cogs_amount) AS order_gross_profit,
        COUNT(DISTINCT o.order_id) AS attributed_orders,
        COUNT(DISTINCT o.customer_id) AS attributed_customers
    FROM oltp.orders o
    JOIN oltp.order_items oi
        ON oi.order_id = o.order_id
    WHERE o.campaign_id IS NOT NULL
    GROUP BY o.campaign_id
)
SELECT
    s.campaign_id,
    s.campaign_code,
    s.campaign_name,
    s.campaign_type,
    s.start_date,
    s.end_date,
    s.budget_amount,
    s.actual_spend,
    s.objective_code,
    s.status_code,
    COALESCE(r.sent_count, 0) AS sent_count,
    COALESCE(r.open_count, 0) AS open_count,
    COALESCE(r.click_count, 0) AS click_count,
    COALESCE(r.convert_count, 0) AS convert_count,
    COALESCE(r.attributed_revenue, 0) AS response_attributed_revenue,
    COALESCE(oa.order_net_sales, 0) AS order_net_sales,
    COALESCE(oa.order_gross_profit, 0) AS order_gross_profit,
    COALESCE(oa.attributed_orders, 0) AS attributed_orders,
    COALESCE(oa.attributed_customers, 0) AS attributed_customers,
    CASE
        WHEN COALESCE(r.sent_count, 0) = 0 THEN NULL
        ELSE ROUND(COALESCE(r.convert_count, 0)::NUMERIC / r.sent_count, 4)
    END AS conversion_rate,
    CASE
        WHEN COALESCE(s.actual_spend, 0) = 0 THEN NULL
        ELSE ROUND(
            (COALESCE(oa.order_gross_profit, 0) - s.actual_spend) / s.actual_spend,
            4
        )
    END AS campaign_roi
FROM spend s
LEFT JOIN responses r
    ON r.campaign_id = s.campaign_id
LEFT JOIN order_attr oa
    ON oa.campaign_id = s.campaign_id;

-- -----------------------------------------------------------------------------
-- Shipment performance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_shipment_performance AS
SELECT
    sh.shipment_id,
    sh.order_id,
    o.order_date,
    sh.dc_id,
    dc.dc_code,
    dc.dc_name,
    sh.store_id,
    sh.carrier_name,
    sh.shipment_status,
    sh.ship_date,
    sh.delivery_date,
    (sh.ship_date - o.order_date) AS fulfillment_lead_time_days,
    (sh.delivery_date - sh.ship_date) AS transit_days,
    CASE
        WHEN sh.ship_date IS NULL THEN 'Not Shipped'
        WHEN (sh.ship_date - o.order_date) > 5 THEN 'Delayed Ship'
        WHEN sh.delivery_date IS NOT NULL AND (sh.delivery_date - sh.ship_date) > 7 THEN 'Delayed Delivery'
        ELSE 'On Track'
    END AS delay_flag
FROM oltp.shipments sh
JOIN oltp.orders o
    ON o.order_id = sh.order_id
LEFT JOIN oltp.distribution_centers dc
    ON dc.dc_id = sh.dc_id;

-- -----------------------------------------------------------------------------
-- Executive daily scorecard grain
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_executive_daily_kpis AS
WITH sales AS (
    SELECT
        order_date,
        SUM(net_sales) AS net_sales,
        SUM(gross_profit) AS gross_profit,
        SUM(order_count) AS order_count,
        SUM(units_sold) AS units_sold
    FROM analytics.vw_sales_daily
    GROUP BY order_date
),
returns AS (
    SELECT
        return_date AS order_date,
        SUM(refund_line_amount) AS refund_amount,
        SUM(quantity_returned) AS units_returned
    FROM analytics.vw_fact_return_line
    GROUP BY return_date
),
stockouts AS (
    SELECT
        snapshot_date AS order_date,
        COUNT(*) FILTER (WHERE quantity_on_hand = 0) AS stockout_positions,
        COUNT(*) AS snapshot_positions
    FROM oltp.inventory_snapshots
    GROUP BY snapshot_date
)
SELECT
    s.order_date,
    s.net_sales,
    s.gross_profit,
    CASE WHEN s.net_sales = 0 THEN NULL ELSE ROUND(s.gross_profit / s.net_sales, 4) END AS margin_pct,
    s.order_count,
    s.units_sold,
    CASE WHEN s.order_count = 0 THEN NULL ELSE ROUND(s.net_sales / s.order_count, 2) END AS aov,
    COALESCE(r.refund_amount, 0) AS refund_amount,
    COALESCE(r.units_returned, 0) AS units_returned,
    COALESCE(so.stockout_positions, 0) AS stockout_positions,
    COALESCE(so.snapshot_positions, 0) AS snapshot_positions
FROM sales s
LEFT JOIN returns r
    ON r.order_date = s.order_date
LEFT JOIN stockouts so
    ON so.order_date = s.order_date;

-- -----------------------------------------------------------------------------
-- Payment mix
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_payment_mix AS
SELECT
    p.payment_method_id,
    pm.method_code,
    pm.method_name,
    pm.method_group,
    DATE_TRUNC('month', p.payment_timestamp)::DATE AS payment_month,
    COUNT(*) AS payment_count,
    SUM(p.payment_amount) AS payment_amount
FROM oltp.payments p
JOIN oltp.payment_methods pm
    ON pm.payment_method_id = p.payment_method_id
WHERE p.payment_status = 'Captured'
GROUP BY
    p.payment_method_id, pm.method_code, pm.method_name, pm.method_group,
    DATE_TRUNC('month', p.payment_timestamp)::DATE;

-- =============================================================================
-- ML prediction staging (load from data/predictions/*.csv — empty until loaded)
-- View returns zero rows when staging tables are empty (no fabricated scores).
-- =============================================================================

CREATE TABLE IF NOT EXISTS analytics.stg_churn_predictions (
    customer_id         BIGINT,
    churn_probability   DOUBLE PRECISION,
    churn_predicted     INTEGER,
    churn_actual        INTEGER,
    model_name          TEXT,
    threshold           DOUBLE PRECISION,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.stg_profit_predictions (
    order_id            BIGINT,
    customer_id         BIGINT,
    order_date          DATE,
    net_sales           NUMERIC,
    margin_pct          DOUBLE PRECISION,
    is_profitable       INTEGER,
    profit_probability  DOUBLE PRECISION,
    profit_predicted    INTEGER,
    model_name          TEXT,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.stg_sales_forecast_predictions (
    ds                  DATE,
    y_true              NUMERIC,
    seasonal_naive      NUMERIC,
    sarimax             NUMERIC,
    sarimax_lower       NUMERIC,
    sarimax_upper       NUMERIC,
    ml_xgboost          NUMERIC,
    forecast_horizon    TEXT,
    yhat                NUMERIC,
    yhat_lower          NUMERIC,
    yhat_upper          NUMERIC,
    model_used          TEXT,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Canonical ML predictions view consumed by MachineLearningService
CREATE OR REPLACE VIEW analytics.vw_ml_predictions AS
SELECT
    COALESCE(NULLIF(TRIM(c.model_name), ''), 'churn_model') AS model_name,
    'customer'::TEXT AS entity_type,
    c.customer_id::TEXT AS entity_id,
    c.customer_id::TEXT AS customer_id,
    c.churn_probability AS score,
    c.churn_probability AS churn_probability,
    CASE
        WHEN c.churn_predicted = 1 THEN 'churn'
        WHEN c.churn_predicted = 0 THEN 'retain'
        ELSE NULL
    END AS label,
    c.loaded_at::DATE AS prediction_date,
    c.loaded_at::DATE AS as_of_date,
    NULL::DOUBLE PRECISION AS confidence,
    COALESCE(NULLIF(TRIM(c.model_name), ''), 'churn_model') AS model_version,
    'stg_churn_predictions'::TEXT AS prediction_source,
    NULL::TEXT AS title,
    NULL::TEXT AS explanation,
    NULL::NUMERIC AS estimated_impact
FROM analytics.stg_churn_predictions c
WHERE c.customer_id IS NOT NULL

UNION ALL

SELECT
    COALESCE(NULLIF(TRIM(p.model_name), ''), 'profit_model') AS model_name,
    'order'::TEXT AS entity_type,
    p.order_id::TEXT AS entity_id,
    p.customer_id::TEXT AS customer_id,
    p.profit_probability AS score,
    NULL::DOUBLE PRECISION AS churn_probability,
    CASE
        WHEN p.profit_predicted = 1 THEN 'profitable'
        WHEN p.profit_predicted = 0 THEN 'unprofitable'
        ELSE NULL
    END AS label,
    COALESCE(p.order_date, p.loaded_at::DATE) AS prediction_date,
    p.loaded_at::DATE AS as_of_date,
    NULL::DOUBLE PRECISION AS confidence,
    COALESCE(NULLIF(TRIM(p.model_name), ''), 'profit_model') AS model_version,
    'stg_profit_predictions'::TEXT AS prediction_source,
    NULL::TEXT AS title,
    NULL::TEXT AS explanation,
    p.net_sales AS estimated_impact
FROM analytics.stg_profit_predictions p
WHERE p.order_id IS NOT NULL

UNION ALL

SELECT
    COALESCE(
        NULLIF(TRIM(f.model_used), ''),
        NULLIF(TRIM(f.forecast_horizon), ''),
        'sales_forecast'
    ) AS model_name,
    'forecast'::TEXT AS entity_type,
    TO_CHAR(f.ds, 'YYYY-MM-DD') AS entity_id,
    NULL::TEXT AS customer_id,
    COALESCE(f.yhat, f.ml_xgboost, f.sarimax, f.seasonal_naive) AS score,
    NULL::DOUBLE PRECISION AS churn_probability,
    'sales_forecast'::TEXT AS label,
    f.ds AS prediction_date,
    f.loaded_at::DATE AS as_of_date,
    NULL::DOUBLE PRECISION AS confidence,
    COALESCE(NULLIF(TRIM(f.model_used), ''), 'sales_forecast') AS model_version,
    'stg_sales_forecast_predictions'::TEXT AS prediction_source,
    'Sales forecast'::TEXT AS title,
    f.forecast_horizon AS explanation,
    COALESCE(f.yhat, f.ml_xgboost, f.sarimax, f.seasonal_naive) AS estimated_impact
FROM analytics.stg_sales_forecast_predictions f
WHERE f.ds IS NOT NULL;

-- =============================================================================
-- Data quality summary (computed from oltp — no fabricated scores)
-- One row per check; includes overall rollup when source tables have rows.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.vw_data_quality_summary AS
WITH src AS (
    SELECT 'oltp.customers'::TEXT AS entity_name,
           COUNT(*)::NUMERIC AS row_count,
           COUNT(*) FILTER (
               WHERE email_hash IS NULL OR BTRIM(email_hash) = ''
           )::NUMERIC AS missing_critical,
           COUNT(*)::NUMERIC - COUNT(DISTINCT customer_id)::NUMERIC AS duplicate_keys,
           MAX(updated_at) AS last_updated
    FROM oltp.customers
    UNION ALL
    SELECT 'oltp.orders',
           COUNT(*)::NUMERIC,
           COUNT(*) FILTER (WHERE customer_id IS NULL OR channel_id IS NULL)::NUMERIC,
           COUNT(*)::NUMERIC - COUNT(DISTINCT order_id)::NUMERIC,
           MAX(updated_at)
    FROM oltp.orders
    UNION ALL
    SELECT 'oltp.order_items',
           COUNT(*)::NUMERIC,
           COUNT(*) FILTER (WHERE oi.order_id IS NULL OR oi.product_id IS NULL)::NUMERIC,
           COUNT(*)::NUMERIC - COUNT(DISTINCT oi.order_item_id)::NUMERIC,
           MAX(o.updated_at)
    FROM oltp.order_items oi
    LEFT JOIN oltp.orders o ON o.order_id = oi.order_id
    UNION ALL
    SELECT 'oltp.products',
           COUNT(*)::NUMERIC,
           COUNT(*) FILTER (WHERE sku IS NULL OR BTRIM(sku) = '')::NUMERIC,
           COUNT(*)::NUMERIC - COUNT(DISTINCT product_id)::NUMERIC,
           MAX(updated_at)
    FROM oltp.products
    UNION ALL
    SELECT 'oltp.inventory',
           COUNT(*)::NUMERIC,
           COUNT(*) FILTER (WHERE product_id IS NULL)::NUMERIC,
           0::NUMERIC,
           MAX(as_of_timestamp)
    FROM oltp.inventory
),
per_table AS (
    SELECT
        entity_name,
        row_count,
        CASE WHEN row_count > 0
             THEN ROUND(1 - (missing_critical / NULLIF(row_count, 0)), 6)
             ELSE NULL
        END AS completeness,
        CASE WHEN row_count > 0
             THEN ROUND(missing_critical / NULLIF(row_count, 0), 6)
             ELSE NULL
        END AS missing_value_pct,
        CASE WHEN row_count > 0
             THEN ROUND(GREATEST(duplicate_keys, 0) / NULLIF(row_count, 0), 6)
             ELSE NULL
        END AS duplicate_pct,
        CASE WHEN row_count > 0 AND missing_critical = 0 THEN 1.0
             WHEN row_count > 0 THEN ROUND(1 - (missing_critical / NULLIF(row_count, 0)), 6)
             ELSE NULL
        END AS validity,
        CASE WHEN row_count > 0 AND duplicate_keys = 0 THEN 1.0
             WHEN row_count > 0 THEN ROUND(1 - (GREATEST(duplicate_keys, 0) / NULLIF(row_count, 0)), 6)
             ELSE NULL
        END AS consistency,
        last_updated,
        CASE
            WHEN last_updated IS NULL THEN NULL
            ELSE ROUND(
                GREATEST(
                    0::NUMERIC,
                    1 - (EXTRACT(EPOCH FROM (NOW() - last_updated)) / (86400.0 * 30))
                )::NUMERIC,
                6
            )
        END AS freshness
    FROM src
),
scored AS (
    SELECT
        entity_name,
        row_count,
        completeness,
        missing_value_pct,
        duplicate_pct,
        validity,
        consistency,
        freshness,
        last_updated,
        ROUND(
            (
                COALESCE(completeness, 0)
                + COALESCE(validity, 0)
                + COALESCE(consistency, 0)
                + COALESCE(freshness, 0)
            ) / NULLIF(
                (CASE WHEN completeness IS NULL THEN 0 ELSE 1 END
                 + CASE WHEN validity IS NULL THEN 0 ELSE 1 END
                 + CASE WHEN consistency IS NULL THEN 0 ELSE 1 END
                 + CASE WHEN freshness IS NULL THEN 0 ELSE 1 END),
                0
            ),
            6
        ) AS score
    FROM per_table
),
metric_rows AS (
    SELECT
        CURRENT_DATE AS check_date,
        CURRENT_DATE AS as_of_date,
        'completeness'::TEXT AS check_name,
        entity_name,
        'table'::TEXT AS namespace,
        completeness AS score,
        CASE
            WHEN completeness IS NULL THEN 'unknown'
            WHEN completeness < 0.7 THEN 'critical'
            WHEN completeness < 0.9 THEN 'high'
            ELSE 'info'
        END AS severity,
        format('Missing critical fields pct=%s', COALESCE(missing_value_pct::TEXT, 'n/a')) AS message,
        'Share of rows with required fields populated'::TEXT AS description,
        NULL::NUMERIC AS overall_score,
        NULL::NUMERIC AS dq_score,
        NULL::NUMERIC AS quality_score,
        'Data Platform'::TEXT AS owner,
        missing_value_pct,
        duplicate_pct,
        freshness,
        validity,
        consistency,
        completeness,
        row_count AS invalid_records_proxy
    FROM scored

    UNION ALL

    SELECT
        CURRENT_DATE, CURRENT_DATE,
        'duplicates', entity_name, 'table',
        consistency,
        CASE
            WHEN consistency IS NULL THEN 'unknown'
            WHEN consistency < 0.7 THEN 'critical'
            WHEN consistency < 0.9 THEN 'high'
            ELSE 'info'
        END,
        format('Duplicate key pct=%s', COALESCE(duplicate_pct::TEXT, 'n/a')),
        'Primary-key uniqueness pressure (approx)',
        NULL, NULL, NULL, 'Data Platform',
        missing_value_pct, duplicate_pct, freshness, validity, consistency, completeness, row_count
    FROM scored

    UNION ALL

    SELECT
        CURRENT_DATE, CURRENT_DATE,
        'freshness', entity_name, 'table',
        freshness,
        CASE
            WHEN freshness IS NULL THEN 'unknown'
            WHEN freshness < 0.5 THEN 'critical'
            WHEN freshness < 0.8 THEN 'high'
            ELSE 'info'
        END,
        format('Last updated=%s', COALESCE(last_updated::TEXT, 'n/a')),
        'Recency of source table updates (30-day decay)',
        NULL, NULL, NULL, 'Data Platform',
        missing_value_pct, duplicate_pct, freshness, validity, consistency, completeness, row_count
    FROM scored

    UNION ALL

    SELECT
        CURRENT_DATE, CURRENT_DATE,
        'validity', entity_name, 'table',
        validity,
        CASE
            WHEN validity IS NULL THEN 'unknown'
            WHEN validity < 0.7 THEN 'critical'
            WHEN validity < 0.9 THEN 'high'
            ELSE 'info'
        END,
        format('Invalid/missing critical=%s', COALESCE(missing_value_pct::TEXT, 'n/a')),
        'Validity derived from required-field population',
        NULL, NULL, NULL, 'Data Platform',
        missing_value_pct, duplicate_pct, freshness, validity, consistency, completeness, row_count
    FROM scored

    UNION ALL

    SELECT
        CURRENT_DATE, CURRENT_DATE,
        'table_score', entity_name, 'table',
        score,
        CASE
            WHEN score IS NULL THEN 'unknown'
            WHEN score < 0.7 THEN 'critical'
            WHEN score < 0.9 THEN 'high'
            ELSE 'info'
        END,
        format('Composite DQ score=%s', COALESCE(score::TEXT, 'n/a')),
        'Mean of available completeness/validity/consistency/freshness',
        NULL, NULL, NULL, 'Data Platform',
        missing_value_pct, duplicate_pct, freshness, validity, consistency, completeness, row_count
    FROM scored
),
overall AS (
    SELECT AVG(score) AS overall_score
    FROM scored
    WHERE score IS NOT NULL
)
SELECT
    m.check_date,
    m.as_of_date,
    m.check_name,
    m.entity_name,
    m.namespace,
    m.score,
    m.severity,
    m.message,
    m.description,
    o.overall_score,
    o.overall_score AS dq_score,
    o.overall_score AS quality_score,
    m.owner,
    m.missing_value_pct,
    m.duplicate_pct,
    m.freshness,
    m.validity,
    m.consistency,
    m.completeness,
    m.invalid_records_proxy AS invalid_records
FROM metric_rows m
CROSS JOIN overall o

UNION ALL

SELECT
    CURRENT_DATE,
    CURRENT_DATE,
    'overall_score',
    'analytics.platform',
    'overall',
    o.overall_score,
    CASE
        WHEN o.overall_score IS NULL THEN 'unknown'
        WHEN o.overall_score < 0.7 THEN 'critical'
        WHEN o.overall_score < 0.9 THEN 'high'
        ELSE 'info'
    END,
    format('Platform overall DQ score=%s', COALESCE(o.overall_score::TEXT, 'n/a')),
    'Average of per-table composite scores (NULL when no oltp rows)',
    o.overall_score,
    o.overall_score,
    o.overall_score,
    'Data Platform',
    NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM overall o;
