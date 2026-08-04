-- =============================================================================
-- Migration: align ck_labor_hours with store × day (optional employee) grain
-- =============================================================================
-- Context
--   Architecture (docs/02, docs/03) defines store_labor_hours primarily as
--   store × day labor input for sales-per-labor-hour KPIs. employee_id is
--   optional for finer grain. The generator emits store-day aggregates
--   (typically ~60–320 hours/day) with employee_id NULL.
--
--   The original CHECK (labor_hours <= 24) assumes employee-shift grain only
--   and rejects valid store-day aggregates.
--
-- Apply on Neon (already deployed schema):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/001_fix_ck_store_labor_hours.sql
--
-- Then resume OLTP load:
--   python scripts/load_database.py --data-dir "..." --verbose
-- =============================================================================

BEGIN;

ALTER TABLE oltp.store_labor_hours
    DROP CONSTRAINT IF EXISTS ck_labor_hours;

-- Primary grain: store × day aggregate (employee_id IS NULL) → multi-FTE hours.
-- Optional grain: employee × day (employee_id present) → single-shift hours ≤ 24.
ALTER TABLE oltp.store_labor_hours
    ADD CONSTRAINT ck_labor_hours CHECK (
        labor_hours > 0
        AND (
            (employee_id IS NULL AND labor_hours <= 500)
            OR (employee_id IS NOT NULL AND labor_hours <= 24)
        )
    );

COMMIT;
