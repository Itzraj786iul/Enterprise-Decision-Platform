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
