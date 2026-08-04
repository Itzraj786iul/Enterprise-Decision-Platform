-- =============================================================================
-- Enterprise Business Analytics & Decision Intelligence Platform
-- Foundational Analytics Views (OLTP-facing)
-- =============================================================================
-- Intent: thin, transparent views that expose clean grains for later marts.
-- No complex KPI business logic yet — only structural / lightly derived fields.
-- =============================================================================

SET search_path TO oltp, public;

-- -----------------------------------------------------------------------------
-- Master / conformed helpers
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_dim_store_base AS
SELECT
    s.store_id,
    s.store_code,
    s.store_name,
    s.store_format,
    s.region_id,
    r.region_code,
    r.region_name,
    s.city,
    s.state_code,
    s.selling_sq_ft,
    s.open_date,
    s.close_date,
    s.is_active
FROM stores s
JOIN regions r ON r.region_id = s.region_id;

CREATE OR REPLACE VIEW vw_dim_product_base AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    p.brand_name,
    p.category_id,
    c.category_code,
    c.category_name,
    c.category_level,
    c.parent_category_id,
    p.primary_supplier_id,
    s.supplier_code,
    s.supplier_name,
    p.current_list_price,
    p.current_unit_cost,
    p.popularity_score,
    p.is_active,
    p.launch_date,
    p.discontinue_date
FROM products p
JOIN product_categories c ON c.category_id = p.category_id
LEFT JOIN suppliers s ON s.supplier_id = p.primary_supplier_id;

CREATE OR REPLACE VIEW vw_dim_customer_base AS
SELECT
    cu.customer_id,
    cu.customer_number,
    cu.customer_type,
    cu.registration_date,
    cu.acquisition_channel_id,
    ch.channel_name AS acquisition_channel_name,
    cu.preferred_store_id,
    cu.is_active,
    la.loyalty_account_id,
    la.loyalty_number,
    la.tier_code AS loyalty_tier,
    la.points_balance,
    la.status_code AS loyalty_status
FROM customers cu
LEFT JOIN channels ch ON ch.channel_id = cu.acquisition_channel_id
LEFT JOIN loyalty_accounts la ON la.customer_id = cu.customer_id;

-- -----------------------------------------------------------------------------
-- Sales foundations
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_order_header AS
SELECT
    o.order_id,
    o.order_number,
    o.customer_id,
    o.store_id,
    o.channel_id,
    ch.channel_code,
    ch.channel_name,
    o.order_date,
    o.order_timestamp,
    o.order_status,
    o.gross_amount,
    o.discount_amount,
    o.net_amount,
    o.tax_amount,
    o.shipping_amount,
    o.total_amount,
    o.employee_id,
    o.campaign_id,
    d.year_number,
    d.month_number,
    d.quarter_number,
    d.season_name
FROM orders o
JOIN channels ch ON ch.channel_id = o.channel_id
JOIN calendar_date d ON d.full_date = o.order_date;

CREATE OR REPLACE VIEW vw_order_lines AS
SELECT
    oi.order_item_id,
    oi.order_id,
    o.order_number,
    o.order_date,
    o.customer_id,
    o.store_id,
    o.channel_id,
    o.campaign_id,
    oi.line_number,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.discount_amount,
    oi.line_gross_amount,
    oi.line_net_amount,
    oi.line_cogs_amount,
    (oi.line_net_amount - oi.line_cogs_amount) AS line_gross_profit,
    oi.promotion_id,
    oi.is_gift
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id;

CREATE OR REPLACE VIEW vw_sales_daily_base AS
SELECT
    o.order_date,
    o.store_id,
    o.channel_id,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(oi.order_item_id) AS line_count,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.line_gross_amount) AS gross_sales,
    SUM(oi.discount_amount) AS discount_amount,
    SUM(oi.line_net_amount) AS net_sales,
    SUM(oi.line_cogs_amount) AS cogs_amount,
    SUM(oi.line_net_amount - oi.line_cogs_amount) AS gross_profit
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Completed', 'Returned', 'PartiallyReturned')
GROUP BY o.order_date, o.store_id, o.channel_id;

-- -----------------------------------------------------------------------------
-- Payments / fulfillment / returns foundations
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_payments_base AS
SELECT
    p.payment_id,
    p.order_id,
    o.order_date,
    o.customer_id,
    o.store_id,
    o.channel_id,
    p.payment_method_id,
    pm.method_code,
    pm.method_name,
    p.payment_timestamp,
    p.payment_amount,
    p.payment_status
FROM payments p
JOIN orders o ON o.order_id = p.order_id
JOIN payment_methods pm ON pm.payment_method_id = p.payment_method_id;

CREATE OR REPLACE VIEW vw_shipments_base AS
SELECT
    s.shipment_id,
    s.order_id,
    o.order_date,
    s.dc_id,
    s.store_id,
    s.carrier_name,
    s.shipment_status,
    s.ship_date,
    s.delivery_date,
    CASE
        WHEN s.ship_date IS NOT NULL THEN (s.ship_date - o.order_date)
        ELSE NULL
    END AS fulfillment_lead_time_days
FROM shipments s
JOIN orders o ON o.order_id = s.order_id;

CREATE OR REPLACE VIEW vw_returns_base AS
SELECT
    r.return_id,
    r.order_id,
    r.customer_id,
    r.return_date,
    r.return_status,
    r.refund_amount,
    o.order_date,
    (r.return_date - o.order_date) AS days_to_return
FROM returns r
JOIN orders o ON o.order_id = r.order_id;

CREATE OR REPLACE VIEW vw_return_lines AS
SELECT
    ri.return_item_id,
    ri.return_id,
    r.return_date,
    r.order_id,
    r.customer_id,
    ri.order_item_id,
    ri.product_id,
    ri.quantity_returned,
    ri.unit_refund_amount,
    (ri.quantity_returned * ri.unit_refund_amount) AS refund_line_amount,
    ri.restock_flag,
    ri.return_reason_code
FROM return_items ri
JOIN returns r ON r.return_id = ri.return_id;

-- -----------------------------------------------------------------------------
-- Inventory / procurement foundations
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_inventory_current AS
SELECT
    i.inventory_id,
    i.product_id,
    i.location_type,
    i.store_id,
    i.dc_id,
    i.quantity_on_hand,
    i.quantity_reserved,
    i.quantity_available,
    i.reorder_point,
    i.max_stock,
    p.current_unit_cost,
    (i.quantity_on_hand * p.current_unit_cost) AS inventory_value_cost,
    i.as_of_timestamp
FROM inventory i
JOIN products p ON p.product_id = i.product_id;

CREATE OR REPLACE VIEW vw_inventory_snapshots_base AS
SELECT
    s.snapshot_id,
    s.snapshot_date,
    s.product_id,
    s.location_type,
    s.store_id,
    s.dc_id,
    s.quantity_on_hand,
    s.quantity_reserved,
    s.quantity_available,
    s.inventory_value_cost,
    d.year_number,
    d.month_number,
    d.week_of_year
FROM inventory_snapshots s
JOIN calendar_date d ON d.full_date = s.snapshot_date;

CREATE OR REPLACE VIEW vw_purchase_order_lines AS
SELECT
    poi.po_item_id,
    poi.purchase_order_id,
    po.po_number,
    po.supplier_id,
    po.dc_id,
    po.order_date,
    po.expected_receipt_date,
    po.po_status,
    poi.line_number,
    poi.product_id,
    poi.quantity_ordered,
    poi.unit_cost,
    (poi.quantity_ordered * poi.unit_cost) AS ordered_amount
FROM purchase_order_items poi
JOIN purchase_orders po ON po.purchase_order_id = poi.purchase_order_id;

CREATE OR REPLACE VIEW vw_receipt_lines AS
SELECT
    gri.receipt_item_id,
    gri.receipt_id,
    gr.purchase_order_id,
    gr.dc_id,
    gr.receipt_date,
    gr.is_on_time,
    gri.po_item_id,
    gri.product_id,
    gri.quantity_received
FROM goods_receipt_items gri
JOIN goods_receipts gr ON gr.receipt_id = gri.receipt_id;

-- -----------------------------------------------------------------------------
-- Marketing foundations
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_campaigns_base AS
SELECT
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    c.campaign_type,
    c.channel_id,
    ch.channel_name,
    c.start_date,
    c.end_date,
    c.budget_amount,
    c.actual_spend,
    c.objective_code,
    c.lift_factor,
    c.status_code
FROM marketing_campaigns c
LEFT JOIN channels ch ON ch.channel_id = c.channel_id;

CREATE OR REPLACE VIEW vw_campaign_responses_base AS
SELECT
    cr.campaign_response_id,
    cr.campaign_id,
    c.campaign_code,
    cr.customer_id,
    cr.response_timestamp,
    cr.response_type,
    cr.order_id,
    cr.attributed_revenue
FROM campaign_responses cr
JOIN marketing_campaigns c ON c.campaign_id = cr.campaign_id;

-- -----------------------------------------------------------------------------
-- Calendar helper
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_calendar AS
SELECT
    date_id,
    full_date,
    day_of_week,
    day_name,
    week_of_year,
    month_number,
    month_name,
    quarter_number,
    year_number,
    fiscal_year,
    fiscal_quarter,
    is_weekend,
    is_holiday,
    holiday_name,
    season_name
FROM calendar_date;
