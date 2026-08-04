-- Load ML prediction CSVs into analytics staging tables.
-- Run after analytical_views.sql (staging tables must exist).
-- From repository root (enterprise-decision-platform):
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/load_ml_predictions.sql
--
-- Paths below are relative to the psql client working directory (repo root).

BEGIN;

TRUNCATE analytics.stg_churn_predictions;
TRUNCATE analytics.stg_profit_predictions;
TRUNCATE analytics.stg_sales_forecast_predictions;

\copy analytics.stg_churn_predictions (customer_id, churn_probability, churn_predicted, churn_actual, model_name, threshold) FROM 'data/predictions/churn_predictions.csv' WITH (FORMAT csv, HEADER true)

\copy analytics.stg_profit_predictions (order_id, customer_id, order_date, net_sales, margin_pct, is_profitable, profit_probability, profit_predicted, model_name) FROM 'data/predictions/profit_predictions.csv' WITH (FORMAT csv, HEADER true)

\copy analytics.stg_sales_forecast_predictions (ds, y_true, seasonal_naive, sarimax, sarimax_lower, sarimax_upper, ml_xgboost, forecast_horizon, yhat, yhat_lower, yhat_upper, model_used) FROM 'data/predictions/sales_forecast_predictions.csv' WITH (FORMAT csv, HEADER true)

COMMIT;

-- Optional verification
-- SELECT prediction_source, COUNT(*) FROM analytics.vw_ml_predictions GROUP BY 1;
